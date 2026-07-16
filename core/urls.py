from django.urls import path
from . import views

urlpatterns = [
    # 🟢 Feeds & Opinions
    path('topics/', views.TopicListView.as_view(), name='topics'),
    path('opinions/', views.OpinionListCreateView.as_view(), name='opinions'),
    path('opinions/<int:opinion_id>/edit/', views.EditOpinionView.as_view(), name='edit_opinion'),
    path('opinions/<int:opinion_id>/delete/', views.DeleteOpinionView.as_view(), name='delete_opinion'),
    path('opinions/<int:opinion_id>/like/', views.LikeOpinionView.as_view(), name='like_opinion'),
    path('opinions/<int:opinion_id>/boost/', views.OpinionBoostView.as_view(), name='boost_opinion'),
    path('opinions/<int:opinion_id>/replies/', views.OpinionReplyListCreateView.as_view(), name='opinion_replies'),
    path('boost-status/', views.BoostStatusView.as_view(), name='boost_status'),
    
    # 🟢 Reports
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    
    # 🟢 Battle Arena
    path('battles/', views.BattleArenaListView.as_view(), name='battles_list'),
    path('battles/create/', views.BattleArenaCreateView.as_view(), name='create_battle'),
    path('battles/<int:battle_id>/vote/', views.BattleArenaVoteView.as_view(), name='vote_battle'),
    path('battles/<int:battle_id>/vote/', views.BattleArenaVoteView.as_view(), name='battle-vote'),

    # 🟢 Feedback
    path('feedback/', views.SubmitFeedbackView.as_view(), name='submit_feedback'),
    
    # 🟢 Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/deleted/', views.TrashNotificationsView.as_view(), name='trashed_notifications'),
    path('notifications/<int:pk>/delete/', views.DeleteNotificationView.as_view(), name='delete_notification'),
    path('notifications/<int:pk>/restore/', views.RestoreNotificationView.as_view(), name='restore_notification'),
    path('notifications/unread-count/', views.NotificationUnreadCountView.as_view(), name='unread_count'),
    path('notifications/<int:pk>/mark-read/', views.MarkSingleNotificationReadView.as_view(), name='mark_single_read'),
    
    # 🟢 Replies (Comments) Management
    path('replies/<int:reply_id>/', views.ReplyDetailView.as_view(), name='reply_detail'), # Handles EDIT and DELETE
    path('replies/<int:reply_id>/like/', views.LikeReplyView.as_view(), name='like_reply'),
    path('replies/<int:reply_id>/report/', views.ReportReplyView.as_view(), name='report_reply'),
]