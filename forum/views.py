from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TopicCircle, Post, Comment, Report
from .forms import GUserCreationForm



# 主页视图（已存在）
def home(request):
    circles = TopicCircle.objects.filter(is_active=True)
    popular_posts = Post.objects.order_by('-likes')[:5]
    return render(request, 'forum/home.html', {'circles': circles, 'popular_posts': popular_posts})

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
        if content:
            Comment.objects.create(
                user=request.user,
                post=post,
                content=content
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