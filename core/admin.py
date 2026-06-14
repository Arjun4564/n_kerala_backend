from django.contrib import admin

from .models import (
    Topic,
    Opinion,
    OpinionLike,
    OpinionBoost,
    OpinionReply,
    Report,
    AvasthaMood,
    Battle,
    BattleVote,
    Badge,
    UserBadge,
    Notification,
    BattleArena,
    BattleOption,
    BattleArenaVote,
)





admin.site.register(Topic)
admin.site.register(Opinion)
admin.site.register(OpinionLike)
admin.site.register(OpinionBoost)
admin.site.register(OpinionReply)
admin.site.register(Report)
admin.site.register(AvasthaMood)
admin.site.register(Battle)
admin.site.register(BattleVote)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Notification)
admin.site.register(BattleArena)
admin.site.register(BattleOption)
admin.site.register(BattleArenaVote)