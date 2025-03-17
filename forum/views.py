from functools import wraps

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TopicCircle, Post, Comment, Report
from .forms import GUserCreationForm, NicknameForm, TopicCircleForm


# 主页视图（已存在）
def home(request):
    # circles = TopicCircle.objects.filter(is_active=True)
    # popular_posts = Post.objects.order_by('-likes')[:5]
    # return render(request, 'forum/home.html', {'circles': circles, 'popular_posts': popular_posts})
    circles = TopicCircle.objects.filter(is_active=True).annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:5]
    return render(request, 'forum/home.html', {'circles': circles})

# 注册视图
def register(request):
    if request.method == 'POST':
        form = GUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 注册后自动登录
            messages.success(request, f"欢迎 {user.username}，注册成功！")
            return redirect('home')
        else:
            messages.error(request, "注册失败，请检查输入信息。")
    else:
        form = GUserCreationForm()
    return render(request, 'forum/register.html', {'form': form})

# 自定义登录视图（可选，如果你想覆盖默认的）
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"欢迎回来，{user.username}！")
            return redirect('home')
        else:
            messages.error(request, "用户名或密码错误。")
    return render(request, 'forum/templates/registration/templates/forum/login.html')

#
# @login_required
# def circle_detail(request, circle_id):
#     circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
#     posts = Post.objects.filter(circle=circle).order_by('-created_at')
#     return render(request, 'forum/circle_detail.html', {'circle': circle, 'posts': posts})
@login_required
def circle_detail(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    posts = Post.objects.filter(circle=circle).order_by('-created_at')
    return render(request, 'forum/circle_detail.html', {'circle': circle, 'posts': posts})

@login_required
def create_post(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id, is_active=True)
    if request.method == 'POST':
        content = request.POST.get('content')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        nickname = request.POST.get('nickname') if is_anonymous else None
        location = request.POST.get('location') if request.POST.get('location') else None

        # 验证匿名昵称是否在用户绑定的昵称列表中
        if is_anonymous and nickname and nickname not in request.user.anonymous_nicknames:
            messages.error(request, "请使用已绑定的匿名昵称！")
            return render(request, 'forum/create_post.html', {'circle': circle})

        post = Post.objects.create(
            user=request.user,
            circle=circle,
            content=content,
            is_anonymous=is_anonymous,
            nickname=nickname,
            location=location
        )
        messages.success(request, '帖子创建成功！')
        return redirect('circle_detail', circle_id=circle.id)
    return render(request, 'forum/create_post.html', {'circle': circle})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.likes += 1
    post.save()
    messages.success(request, '点赞成功！')
    return redirect('circle_detail', circle_id=post.circle.id)

@login_required
def dislike_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.dislikes += 1
    post.save()
    messages.success(request, '已踩！')
    return redirect('circle_detail', circle_id=post.circle.id)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        nickname = request.POST.get('nickname') if is_anonymous else None

        if is_anonymous and nickname:
            if not request.user.anonymous_nicknames or nickname not in request.user.anonymous_nicknames:
                messages.error(request, "请使用已绑定的匿名昵称！")
                return render(request, 'forum/add_comment.html', {'post': post})

        if content:
            Comment.objects.create(
                user=request.user,
                post=post,
                content=content,
                is_anonymous=is_anonymous,
                nickname=nickname
            )
            messages.success(request, '评论成功！')
        else:
            messages.error(request, '评论内容不能为空！')
        return redirect('circle_detail', circle_id=post.circle.id)
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
            messages.success(request, '举报已提交！')
        else:
            messages.error(request, '请提供举报原因！')
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
            'id': circle.id,  # 确保 id 是有效的整数
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
    if request.method == 'POST':
        form = NicknameForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data['nickname']
            user = request.user
            if nickname not in user.anonymous_nicknames:
                user.anonymous_nicknames.append(nickname)
                user.save()
                messages.success(request, f"昵称 '{nickname}' 添加成功！")
            else:
                messages.error(request, "该昵称已存在！")
        else:
            messages.error(request, "昵称无效，请检查输入。")
    elif request.method == 'DELETE':
        nickname = request.POST.get('nickname')  # 从 POST 数据获取要删除的昵称
        if nickname in request.user.anonymous_nicknames:
            request.user.anonymous_nicknames.remove(nickname)
            request.user.save()
            return JsonResponse({'status': 'success', 'message': f"昵称 '{nickname}' 删除成功！"})
        return JsonResponse({'status': 'error', 'message': '昵称不存在！'}, status=400)

    form = NicknameForm()
    return render(request, 'forum/profile.html', {
        'nicknames': request.user.anonymous_nicknames,
        'form': form
    })

# 自定义装饰器：限制管理员访问
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "您没有管理员权限！")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

# 管理员仪表板
@admin_required
def admin_dashboard(request):
    # 未处理的举报
    reports = Report.objects.filter(is_resolved=False).order_by('-created_at')
    # 所有圈子
    circles = TopicCircle.objects.all().order_by('-created_at')
    return render(request, 'forum/admin_dashboard.html', {
        'reports': reports,
        'circles': circles
    })

# 创建圈子
@admin_required
def circle_create(request):
    if request.method == 'POST':
        form = TopicCircleForm(request.POST)
        if form.is_valid():
            circle = form.save(commit=False)
            circle.created_by = request.user
            circle.save()
            messages.success(request, f"圈子 '{circle.name}' 创建成功！")
            return redirect('admin_dashboard')
    else:
        form = TopicCircleForm()
    return render(request, 'forum/circle_create.html', {'form': form})

# 编辑圈子
@admin_required
def circle_edit(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id)
    if request.method == 'POST':
        form = TopicCircleForm(request.POST, instance=circle)
        if form.is_valid():
            form.save()
            messages.success(request, f"圈子 '{circle.name}' 更新成功！")
            return redirect('admin_dashboard')
    else:
        form = TopicCircleForm(instance=circle)
    return render(request, 'forum/circle_edit.html', {'form': form, 'circle': circle})

# 删除圈子
@admin_required
def circle_delete(request, circle_id):
    circle = get_object_or_404(TopicCircle, id=circle_id)
    if request.method == 'POST':
        circle_name = circle.name
        circle.delete()
        messages.success(request, f"圈子 '{circle_name}' 删除成功！")
        return redirect('admin_dashboard')
    return render(request, 'forum/circle_delete.html', {'circle': circle})

# 处理举报
@admin_required
def report_resolve(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        report.is_resolved = True
        report.save()
        messages.success(request, "举报已标记为已处理！")
        return redirect('admin_dashboard')
    return render(request, 'forum/report_resolve.html', {'report': report})

# 删除帖子
@admin_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "帖子已删除！")
        return redirect('admin_dashboard')
    return render(request, 'forum/post_delete.html', {'post': post})