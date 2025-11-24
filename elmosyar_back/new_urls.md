

| old URLs | new URLs |
|-----------|-----------|
| **Authentication** | |
| `http://89.106.206.119:8000/api/signup/` | `http://89.106.206.119:8000/api/accounts/signup/` |
| `http://89.106.206.119:8000/api/login/` | `http://89.106.206.119:8000/api/accounts/login/` |
| `http://89.106.206.119:8000/api/logout/` | `http://89.106.206.119:8000/api/accounts/logout/` |
| `http://89.106.206.119:8000/api/token/verify/` | `http://89.106.206.119:8000/api/accounts/token/verify/` |
| `http://89.106.206.119:8000/api/token/refresh/` | `http://89.106.206.119:8000/api/accounts/token/refresh/` |
| `http://89.106.206.119:8000/api/verify-email/<str:token>/` | `http://89.106.206.119:8000/api/accounts/verify-email/<str:token>/` |
| `http://89.106.206.119:8000/api/resend-verification-email/` | `http://89.106.206.119:8000/api/accounts/resend-verification-email/` |
| `http://89.106.206.119:8000/api/password-reset/request/` | `http://89.106.206.119:8000/api/accounts/password-reset/request/` |
| `http://89.106.206.119:8000/api/password-reset/<str:token>/` | `http://89.106.206.119:8000/api/accounts/password-reset/<str:token>/` |

| **Profile** | |
| `http://89.106.206.119:8000/api/profile/` | `http://89.106.206.119:8000/api/accounts/profile/` |
| `http://89.106.206.119:8000/api/profile/update/` | `http://89.106.206.119:8000/api/accounts/profile/update/` |
| `http://89.106.206.119:8000/api/profile/update-picture/` | `http://89.106.206.119:8000/api/accounts/profile/update-picture/` |
| `http://89.106.206.119:8000/api/profile/delete-picture/` | `http://89.106.206.119:8000/api/accounts/profile/delete-picture/` |
| `http://89.106.206.119:8000/api/users/<str:username>/profile/` | `http://89.106.206.119:8000/api/accounts/users/<str:username>/profile/` |

| **Social & Follow** | |
| `http://89.106.206.119:8000/api/users/<str:username>/follow/` | `http://89.106.206.119:8000/api/social/users/<str:username>/follow/` |
| `http://89.106.206.119:8000/api/users/<str:username>/unfollow/` | `http://89.106.206.119:8000/api/social/users/<str:username>/unfollow/` |
| `http://89.106.206.119:8000/api/users/<str:username>/followers/` | `http://89.106.206.119:8000/api/social/users/<str:username>/followers/` |
| `http://89.106.206.119:8000/api/users/<str:username>/following/` | `http://89.106.206.119:8000/api/social/users/<str:username>/following/` |

| **Posts** | |
| `http://89.106.206.119:8000/api/posts/` | `http://89.106.206.119:8000/api/posts/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/repost/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/repost/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/thread/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/thread/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/save/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/save/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/unsave/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/unsave/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/delete/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/delete/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/update/` | `http://89.106.206.119:8000/api/posts/<int:post_id>/update/` |
| `http://89.106.206.119:8000/api/posts/category/<str:category_id>/` | `http://89.106.206.119:8000/api/posts/category/<str:category_id>/` |
| `http://89.106.206.119:8000/api/posts/saved/` | `http://89.106.206.119:8000/api/posts/saved/` |
| `http://89.106.206.119:8000/api/users/<str:username>/posts/` | `http://89.106.206.119:8000/api/posts/users/<str:username>/` |

| **Interactions** | |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/like/` | `http://89.106.206.119:8000/api/interactions/posts/<int:post_id>/like/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/dislike/` | `http://89.106.206.119:8000/api/interactions/posts/<int:post_id>/dislike/` |
| `http://89.106.206.119:8000/api/posts/<int:post_id>/comment/` | `http://89.106.206.119:8000/api/interactions/posts/<int:post_id>/comment/` |
| `http://89.106.206.119:8000/api/comments/<int:comment_id>/like/` | `http://89.106.206.119:8000/api/interactions/comments/<int:comment_id>/like/` |
| `http://89.106.206.119:8000/api/comments/<int:comment_id>/delete/` | `http://89.106.206.119:8000/api/interactions/comments/<int:comment_id>/delete/` |
| `http://89.106.206.119:8000/api/comments/<int:comment_id>/update/` | `http://89.106.206.119:8000/api/interactions/comments/<int:comment_id>/update/` |

| **Messaging** | |
| `http://89.106.206.119:8000/api/conversations/` | `http://89.106.206.119:8000/api/messaging/conversations/` |
| `http://89.106.206.119:8000/api/conversations/<int:conversation_id>/` | `http://89.106.206.119:8000/api/messaging/conversations/<int:conversation_id>/` |
| `http://89.106.206.119:8000/api/conversations/<int:conversation_id>/send/` | `http://89.106.206.119:8000/api/messaging/conversations/<int:conversation_id>/send/` |
| `http://89.106.206.119:8000/api/conversations/start/<str:username>/` | `http://89.106.206.119:8000/api/messaging/conversations/start/<str:username>/` |
| `http://89.106.206.119:8000/api/messages/<int:message_id>/delete/` | `http://89.106.206.119:8000/api/messaging/messages/<int:message_id>/delete/` |
| `http://89.106.206.119:8000/api/messages/<int:message_id>/update/` | `http://89.106.206.119:8000/api/messaging/messages/<int:message_id>/update/` |

| **Notifications** | |
| `http://89.106.206.119:8000/api/notifications/` | `http://89.106.206.119:8000/api/notifications/` |
| `http://89.106.206.119:8000/api/notifications/mark-read/` | `http://89.106.206.119:8000/api/notifications/mark-read/` |