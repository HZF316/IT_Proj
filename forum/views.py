from django.utils import timezone
from functools import wraps
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TopicCircle, Post, Comment, Report, Announcement, GUser, UserCircleFollow
from .forms import GUserCreationForm, NicknameForm, TopicCircleForm, AnnouncementForm
import requests
from django.contrib import messages
from django.db.models import Count, Q
from geopy.geocoders import Nominatim


def home(request):
    circles = TopicCircle.objects.filter(is_active=True).annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:5]
    popular_posts = Post.objects.annotate(
        comment_count=Count('comment')
    ).order_by('-likes', '-comment_count')[:5]
    announcements = Announcement.objects.all()
    recommended_posts = Post.objects.filter(is_recommended=True).order_by('-created_at')[:5]

    followed_circles = []
    if request.user.is_authenticated:
        followed_circles = TopicCircle.objects.filter(
            usercirclefollow__user=request.user,
            is_active=True
        ).annotate(post_count=Count('post'))

    search_query = request.GET.get('search', '')
    search_results = None
    if search_query:
        search_results = {
            'circles': TopicCircle.objects.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query),
                is_active=True
            ).annotate(post_count=Count('post')),
            'posts': Post.objects.filter(
                Q(content__icontains=search_query)
            ).annotate(comment_count=Count('comment'))
        }

    return render(request, 'forum/home.html', {
        'circles': circles,
        'popular_posts': popular_posts,
        'announcements': announcements,
        'recommended_posts': recommended_posts,
        'followed_circles': followed_circles,
        'search_query': search_query,
        'search_results': search_results
    })


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "You are not admin")
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def search(request):
    search_query = request.GET.get('q', '')
    if search_query:
        search_results = {
            'circles': TopicCircle.objects.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query),
                is_active=True
            ).annotate(post_count=Count('post')),
            'posts': Post.objects.filter(
                Q(content__icontains=search_query)
            ).annotate(comment_count=Count('comment'))
        }
    else:
        search_results = {'circles': [], 'posts': []}
    return render(request, 'forum/search_results.html',
                  {'search_results': search_results, 'search_query': search_query})


# register view
def register(request):
    if request.method == 'POST':
        form = GUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically Log In After Registration
            messages.success(request, f"Welcome {user.username}，register successfully！")
            return redirect('home')
        else:
            print(form.errors)
            messages.error(request, "Registration failed, please try again")
    else:
        form = GUserCreationForm()
    return render(request, 'forum/register.html', {'form': form})


# Custom Login View (Optional, if you want to override the default)
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Received: username={username}, password={password}")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back，{user.username}！")
            return redirect('home')
        else:
            messages.error(request, "Username or password is incorrect")
    return render(request, 'registration/login.html')



@login_required
def circle_detail(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    sort_by = request.GET.get('sort', 'created_at_desc')
    sort_options = {
        'created_at_desc': '-created_at',
        'created_at_asc': 'created_at',
        'likes_desc': '-likes',
        'likes_asc': 'likes',
        'comments_desc': '-comment_count',
        'comments_asc': 'comment_count',
    }
    sort_field = sort_options.get(sort_by, '-created_at')

    posts = Post.objects.filter(circle=circle).annotate(
        comment_count=Count('comment')
    ).order_by('-is_pinned', sort_field)

    # check whether user has followed the circle
    is_followed = request.user.is_authenticated and UserCircleFollow.objects.filter(user=request.user,
                                                                                    circle=circle).exists()

    return render(request, 'forum/circle_detail.html', {
        'circle': circle,
        'posts': posts,
        'sort_by': sort_by,
        'is_followed': is_followed
    })


@login_required
def create_post(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    if request.method == 'POST':
        content = request.POST.get('content')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        nickname = request.POST.get('nickname') if is_anonymous else None
        use_location = request.POST.get('use_location') == 'on'
        location = None

        if use_location and 'lat' in request.POST and 'lon' in request.POST:
            lat = request.POST.get('lat')
            lon = request.POST.get('lon')
            geolocator = Nominatim(user_agent="our_circle_app")
            location = geolocator.reverse((lat, lon), language='zh-CN').address if lat and lon else None
            location = location or f"Lat: {lat}, Lon: {lon}"

        if is_anonymous and nickname and nickname not in request.user.anonymous_nicknames:
            messages.error(request, "Please uss a created nickname")
            return redirect('circle_detail', circle_id=circle.id)
        if content:
            Post.objects.create(user=request.user, circle=circle, content=content, is_anonymous=is_anonymous,
                                nickname=nickname, location=location)
            messages.success(request, 'Post Successfully')
        else:
            messages.error(request, 'Content cannot be empty')
        return redirect('circle_detail', circle_id=circle.id)
    return render(request, 'forum/circle_detail.html', {'circle': circle})


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.likes += 1
    post.save()
    messages.success(request, 'Likes Successfully')
    return redirect('circle_detail', circle_id=post.circle.id)


@login_required
def dislike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.dislikes += 1
    post.save()
    messages.success(request, 'Unlikes Successfully')
    return redirect('circle_detail', circle_id=post.circle.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        nickname = request.POST.get('nickname') if is_anonymous else None
        use_location = request.POST.get('use_location') == 'on'
        location = None

        if use_location and 'lat' in request.POST and 'lon' in request.POST:
            lat = request.POST.get('lat')
            lon = request.POST.get('lon')
            geolocator = Nominatim(user_agent="our_circle_app")
            location = geolocator.reverse((lat, lon), language='zh-CN').address if lat and lon else None
            location = location or f"Lat: {lat}, Lon: {lon}"

        if is_anonymous and nickname and nickname not in request.user.anonymous_nicknames:
            messages.error(request, "Please uss a created nickname")
            return redirect('post_detail', post_id=post.id)
        if content:
            Comment.objects.create(user=request.user, post=post, content=content, is_anonymous=is_anonymous,
                                   nickname=nickname, location=location)
            messages.success(request, 'Comment Successfully')
        else:
            messages.error(request, 'Comment cannot be empty')
        return redirect('post_detail', post_id=post.id)
    return render(request, 'forum/add_comment.html', {'post': post})


@login_required
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(
                user=request.user,
                post=post,
                reason=reason
            )
            messages.success(request, 'Report Successfully')
        else:
            messages.error(request, 'Please enter a reason')
        return redirect('circle_detail', circle_id=post.circle.id)
    return render(request, 'forum/report_post.html', {'post': post})


@login_required
def all_circles(request):
    sort_by = request.GET.get('sort', 'name')
    sort_options = {
        'name': 'name',
        'name_desc': '-name',
        'post_count': '-post_count',
        'post_count_asc': 'post_count',
    }
    sort_field = sort_options.get(sort_by, 'name')

    search_query = request.GET.get('search', '')

    circles = TopicCircle.objects.filter(is_active=True).annotate(
        post_count=Count('post')
    )

    if search_query:
        circles = circles.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    circles = circles.order_by(sort_field)

    paginator = Paginator(circles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        circle_data = [{
            'id': circle.id,
            'name': circle.name,
            'description': circle.description,
            'post_count': circle.post_count
        } for circle in page_obj.object_list]
        return JsonResponse({
            'circles': circle_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'sort_by': sort_by,
            'search_query': search_query
        })

    return render(request, 'forum/all_circles.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'search_query': search_query
    })



@login_required
def profile(request):
    sort_by = request.GET.get('sort', 'created_at_desc')
    sort_options = {
        'created_at_desc': '-created_at',
        'created_at_asc': 'created_at',
        'likes_desc': '-likes',
        'likes_asc': 'likes',
    }
    sort_field = sort_options.get(sort_by, '-created_at')
    user_posts = Post.objects.filter(user=request.user).order_by(sort_field)

    followed_circles = TopicCircle.objects.filter(
        usercirclefollow__user=request.user,
        is_active=True
    ).annotate(post_count=Count('post'))

    if request.method == 'POST' and 'nickname' in request.POST:
        form = NicknameForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data['nickname']
            if nickname not in request.user.anonymous_nicknames:
                request.user.anonymous_nicknames.append(nickname)
                request.user.save()
                messages.success(request, f"Nickname '{nickname}' add successfully！")
            else:
                messages.error(request, "Nickname already exists")
    elif request.method == 'DELETE':
        nickname = request.POST.get('nickname')
        if nickname in request.user.anonymous_nicknames:
            request.user.anonymous_nicknames.remove(nickname)
            request.user.save()
            return JsonResponse({'status': 'success', 'message': f"Nickname '{nickname}' delete successfully"})
        return JsonResponse({'status': 'error', 'message': 'Nickname does not exist'}, status=400)

    form = NicknameForm()
    return render(request, 'forum/profile.html', {
        'nicknames': request.user.anonymous_nicknames,
        'form': form,
        'user_posts': user_posts,
        'sort_by': sort_by,
        'followed_circles': followed_circles
    })


# admin dashboard
@admin_required
def admin_dashboard(request):
    reports = Report.objects.filter(is_resolved=False).order_by('-created_at')
    circles = TopicCircle.objects.all().order_by('-created_at')
    announcements = Announcement.objects.all()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    stat_type = request.GET.get('stat_type')
    stats = None

    if start_date and end_date and stat_type:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            if start_date > end_date:
                messages.error(request, "Start date cannot be greater than end date！")
            else:
                if stat_type == 'posts':
                    stats = Post.objects.filter(created_at__range=(start_date, end_date)).count()
                elif stat_type == 'comments':
                    stats = Comment.objects.filter(created_at__range=(start_date, end_date)).count()
                elif stat_type == 'users':
                    stats = GUser.objects.filter(date_joined__range=(start_date, end_date)).count()
        except ValueError:
            messages.error(request, "Illegal format，Please: YYYY-MM-DD！")

    return render(request, 'forum/admin_dashboard.html', {
        'reports': reports,
        'circles': circles,
        'announcements': announcements,
        'stats': stats,
        'start_date': start_date,
        'end_date': end_date,
        'stat_type': stat_type
    })



@admin_required
def circle_create(request):
    if request.method == 'POST':
        form = TopicCircleForm(request.POST)
        if form.is_valid():
            circle = form.save(commit=False)
            circle.created_by = request.user
            circle.save()
            messages.success(request, f"Circle '{circle.name}' created successfully")
            return redirect('admin_dashboard')
    else:
        form = TopicCircleForm()
    return render(request, 'forum/circle_create.html', {'form': form})



@admin_required
def circle_edit(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id)
    if request.method == 'POST':
        form = TopicCircleForm(request.POST, instance=circle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Circle '{circle.name}' updated successfully")
            return redirect('admin_dashboard')
    else:
        form = TopicCircleForm(instance=circle)
    return render(request, 'forum/circle_edit.html', {'form': form, 'circle': circle})



@admin_required
def circle_delete(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id)
    if request.method == 'POST':
        circle_name = circle.name
        circle.delete()
        messages.success(request, f"Circle '{circle_name}' deleted successfully")
        return redirect('admin_dashboard')
    return render(request, 'forum/circle_delete.html', {'circle': circle})


@admin_required
def report_resolve(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        report.is_resolved = True
        report.save()
        messages.success(request, "Report has been resolved")
        return redirect('admin_dashboard')
    return render(request, 'forum/report_resolve.html', {'report': report})


# delete post
@admin_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post has been deleted")
        return redirect('admin_dashboard')
    return render(request, 'forum/post_detail.html', {'post': post})


@admin_required
def announcement_create(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, f"Announcement '{announcement.title}' created successfully")
            return redirect('admin_dashboard')
    else:
        form = AnnouncementForm()
    return render(request, 'forum/announcement_create.html', {'form': form})


def announcement_detail(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.user.is_authenticated and request.user.is_admin:
        return redirect('announcement_manage', announcement_id=announcement.id)
    return render(request, 'forum/announcement_detail.html', {'announcement': announcement})

#Announcement management
@admin_required
def announcement_manage(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                messages.success(request, "Announcement has been updated")
                return redirect('admin_dashboard')
        elif action == 'delete':
            announcement.delete()
            messages.success(request, "Announcement has been deleted")
            return redirect('admin_dashboard')
        elif action == 'toggle_pin':
            announcement.is_pinned = not announcement.is_pinned
            announcement.save()
            messages.success(request, f"Announcement has been{'pinned' if announcement.is_pinned else 'CANCEL PIN'}！")
            return redirect('admin_dashboard')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'forum/announcement_manage.html', {
        'form': form,
        'announcement': announcement
    })


@login_required
def user_post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)  # Ensure That Users Can Only Delete Their Own Posts
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post has been deleted")
        return redirect('profile')
    return render(request, 'forum/user_post_delete.html', {'post': post})



@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    sort_by = request.GET.get('sort', 'created_at_desc')
    sort_options = {
        'created_at_desc': '-created_at',
        'created_at_asc': 'created_at',
        'likes_desc': '-likes',
        'likes_asc': 'likes',
    }
    sort_field = sort_options.get(sort_by, '-created_at')
    comments = Comment.objects.filter(post=post).order_by(sort_field)
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'sort_by': sort_by
    })


#like post
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.likes += 1
    post.save()
    return redirect('post_detail', post_id=post.id)


# unlike post
@login_required
def dislike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.dislikes += 1
    post.save()
    return redirect('post_detail', post_id=post.id)


# make comment
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        nickname = request.POST.get('nickname') if is_anonymous else None
        if is_anonymous and nickname and nickname not in request.user.anonymous_nicknames:
            messages.error(request, "Please enter a valid nickname")
            return redirect('post_detail', post_id=post.id)
        if content:
            Comment.objects.create(user=request.user, post=post, content=content, is_anonymous=is_anonymous,
                                   nickname=nickname)
            messages.success(request, 'Comment has been added')
        else:
            messages.error(request, 'Comment cannot be empty')
    return redirect('post_detail', post_id=post.id)


# report post
@login_required
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(user=request.user, post=post, reason=reason)
            messages.success(request, 'Report has been added')
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, 'Please enter a reason')
    return render(request, 'forum/report_post.html', {'post': post})



@login_required
def user_post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post has been deleted")
        return redirect('profile')
    return render(request, 'forum/user_post_delete.html', {'post': post})


@admin_required
def admin_post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post has been deleted")
        return redirect('admin_dashboard')
    return render(request, 'forum/post_delete.html', {'post': post})


# pin post
@login_required
def pin_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.is_pinned = not post.is_pinned
        post.save()
        messages.success(request, f"Post has been {'pinned' if post.is_pinned else 'CANCEL PIN'}！")
    return redirect('post_detail', post_id=post.id)



# like comment
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.likes += 1
    comment.save()
    return redirect('post_detail', post_id=comment.post.id)


# unlike comment
@login_required
def dislike_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.dislikes += 1
    comment.save()
    return redirect('post_detail', post_id=comment.post.id)


# report comment
@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(user=request.user, post=comment.post, reason=f"Report Comment: {reason}")
            messages.success(request, 'Report has been added')
        else:
            messages.error(request, 'Please enter a reason')
    return redirect('post_detail', post_id=comment.post.id)



@admin_required
def admin_comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comment has been deleted")
        return redirect('post_detail', post_id=comment.post.id)
    return render(request, 'forum/comment_delete.html', {'comment': comment})


@admin_required
def recommend_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.is_recommended = not post.is_recommended
        post.save()
        messages.success(request, f"Post has been {'recommended' if post.is_recommended else 'CANCEL RECOMMENDATION'}！")
        return redirect('post_detail', post_id=post.id)
    return render(request, 'forum/recommend_post.html', {'post': post})


@login_required
def follow_circle(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    if not UserCircleFollow.objects.filter(user=request.user, circle=circle).exists():
        UserCircleFollow.objects.create(user=request.user, circle=circle)
        messages.success(request, f"Followed Circles '{circle.name}'！")
    return redirect('circle_detail', circle_id=circle.id)



@login_required
def unfollow_circle(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    follow = UserCircleFollow.objects.filter(user=request.user, circle=circle)
    if follow.exists():
        follow.delete()
        messages.success(request, f"Unfollowed Circle '{circle.name}'!")
    return redirect('circle_detail', circle_id=circle.id)



def get_weather(request):
    api_key = "f0ce8dd116d0a235d4a54eaa89c9591f"
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    weather_data = None

    if lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        try:
            response = requests.get(url)
            response.raise_for_status()
            weather_data = response.json()
            return JsonResponse({
                'status': 'success',
                'data': {
                    'name': weather_data.get('name', 'Unknown Location'),
                    'temp': weather_data['main']['temp'],
                    'description': weather_data['weather'][0]['description'],
                    'humidity': weather_data['main']['humidity'],
                    'wind_speed': weather_data['wind']['speed'],
                }
            })
        except requests.RequestException as e:
            return JsonResponse({'status': 'error', 'message': 'Can not get the weather, please try later'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'No Location Information'}, status=400)



def geocode(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    api_key = "f0ce8dd116d0a235d4a54eaa89c9591f"

    if lat and lon:
        url = f"https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return JsonResponse({
                    'status': 'success',
                    'location': data[0].get('name', 'Unknown Location')
                })
            return JsonResponse({'status': 'error', 'message': 'Can not resolve location'}, status=400)
        except requests.RequestException as e:
            return JsonResponse({'status': 'error', 'message': 'Can not get the weather, please try later'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'No Location Information'}, status=400)
