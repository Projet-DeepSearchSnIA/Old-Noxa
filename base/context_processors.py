# context_processors.py


def notifications_context(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(
            is_read=False, 
            is_deleted=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}


