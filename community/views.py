from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Comment, Like, Challenge, UserChallenge
from .forms import PostForm


def feed(request):
    """Community feed"""
    posts = Post.objects.all().order_by('-created_at')[:20]
    
    # Get likes for authenticated users
    user_likes = set()
    if request.user.is_authenticated:
        user_likes = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    
    context = {
        'posts': posts,
        'user_likes': user_likes,
    }
    return render(request, 'community/feed.html', context)


@login_required
def create_post(request):
    """Create a community post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('community:feed')
    else:
        form = PostForm()
    
    return render(request, 'community/create_post.html', {'form': form})


@login_required
def like_post(request, post_id):
    """Like/unlike a post"""
    post = get_object_or_404(Post, id=post_id)
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        post.likes_count -= 1
    else:
        post.likes_count += 1
    
    post.save()
    
    return redirect('community:feed')


def challenges(request):
    """List of community challenges"""
    challenges_list = Challenge.objects.all().order_by('-start_date')
    
    # Get user participation
    user_challenges = set()
    if request.user.is_authenticated:
        user_challenges = set(UserChallenge.objects.filter(user=request.user).values_list('challenge_id', flat=True))
    
    context = {
        'challenges': challenges_list,
        'user_challenges': user_challenges,
    }
    return render(request, 'community/challenges.html', context)


def challenge_detail(request, challenge_id):
    """Challenge detail page"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # Get participants ordered by progress
    participants = UserChallenge.objects.filter(challenge=challenge).order_by('-progress')[:10]
    
    # Check if user is participating
    user_challenge = None
    if request.user.is_authenticated:
        try:
            user_challenge = UserChallenge.objects.get(user=request.user, challenge=challenge)
        except UserChallenge.DoesNotExist:
            pass
    
    context = {
        'challenge': challenge,
        'participants': participants,
        'user_challenge': user_challenge,
    }
    return render(request, 'community/challenge_detail.html', context)


@login_required
def join_challenge(request, challenge_id):
    """Join a challenge"""
    challenge = get_object_or_404(Challenge, id=challenge_id)
    
    # Check if already joined
    user_challenge, created = UserChallenge.objects.get_or_create(
        user=request.user,
        challenge=challenge
    )
    
    if created:
        messages.success(request, f'You joined {challenge.name}!')
    else:
        messages.info(request, 'You are already participating in this challenge.')
    
    return redirect('community:challenge_detail', challenge_id=challenge_id)
