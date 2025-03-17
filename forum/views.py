from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import GUserCreationForm
from .models import TopicCircle, Post

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