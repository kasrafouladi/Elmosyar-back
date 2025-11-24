from django.db import models
from django.conf import settings

class UserFollow(models.Model):
    from accounts.models import User
    
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follow_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        db_table = 'core_user_followers'

    def __str__(self):
        return f"{self.follower} follows {self.following}"