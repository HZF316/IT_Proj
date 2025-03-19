// AJAX CSRF Token
$.ajaxSetup({
    headers: { "X-CSRFToken": $("meta[name='csrf-token']").attr("content") }
});

// load weather
function loadWeather() {
    const apiKey = "YOUR_OPENWEATHER_API_KEY";
    fetch(`https://api.openweathermap.org/data/2.5/weather?q=Glasgow&appid=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            const temp = (data.main.temp - 273.15).toFixed(1);
            $("#weather").html(`Glasgow | ${temp}°C`);
        })
        .catch(() => $("#weather").text("Weather unavailable"));
}

// load announcement
function loadAnnouncements() {
    $.get("/api/announcements", function(data) {
        let html = data.map(announcement => `
            <div class="alert alert-info mb-2">
                <strong>${announcement.title}</strong><br>
                ${announcement.content}
            </div>
        `).join("");
        $("#announcements").html(html);
    });
}

// load popular posts
let currentPage = 1;
function loadPosts(page = 1) {
   $.get("/static/mock-data/posts.json", function(data) {
        let html = data.posts.map(post => `
            <div class="card mb-3">
                <div class="card-body">
                    <h6 class="card-title">${post.title}</h6>
                    <p class="card-text">${post.content.substring(0, 100)}...</p>
                    <div class="d-flex justify-content-between">
                        <small class="text-muted">Posted in ${post.circle}</small>
                        <button class="btn btn-sm btn-outline-primary" onclick="votePost(${post.id}, 'up')">
                            👍 ${post.upvotes}
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
        $("#posts-list").append(html);
        currentPage++;
    });
}

// load popular circle
function loadTrendingCircles() {
    $.get("/api/circles/hot", function(data) {
        let html = data.circles.map(circle => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <a href="/circle/${circle.id}" class="text-decoration-none">#${circle.name}</a>
                <span class="badge bg-secondary">${circle.post_count} posts</span>
            </div>
        `).join("");
        $("#trending-circles").html(html);
    });
}

// search
$("#search-input").on("input", function() {
    const keyword = $(this).val();
    if (keyword.length >= 2) {
        $.get(`/api/search?q=${keyword}`, function(data) {
            // 显示搜索结果（示例）
            console.log("Search results:", data);
        });
    }
});

// initial load
$(document).ready(function() {
    loadWeather();
    loadAnnouncements();
    loadPosts();
    loadTrendingCircles();

    // scroll for more posts
    $(window).scroll(function() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            loadPosts(currentPage);
        }
    });
});
$(document).on('click', '.upvote-btn', function() {
    const btn = $(this);
    const postId = btn.data('post-id');

    $.ajax({
        url: `/posts/${postId}/upvote/`,
        method: 'POST',
        headers: {'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')},
        success: function(response) {
            btn.html(`👍 ${response.new_count}`);
        },
        error: function(xhr) {
            alert('Failed to upvote: ' + xhr.responseJSON.error);
        }
    });
});