// =============================================================================
// IN-MEMORY NOTIFICATION STORE
// =============================================================================
// Simple in-memory storage for notifications. Used for local development
// and tests. In production this would be backed by Redis or a database.
// =============================================================================

using System.Collections.Generic;
using System.Linq;

namespace NotificationService
{
    /// <summary>
    /// Stores notifications in memory, keyed by notification ID.
    /// </summary>
    public class InMemoryNotificationStore
    {
        private readonly Dictionary<string, Notification> _notifications = new();

        public void Save(Notification notification)
        {
            _notifications[notification.NotificationId] = notification;
        }

        public Notification? Get(string notificationId)
        {
            return _notifications.TryGetValue(notificationId, out var n) ? n : null;
        }

        public IEnumerable<Notification> GetByUser(string userId)
        {
            return _notifications.Values
                .Where(n => n.UserId == userId)
                .OrderByDescending(n => n.CreatedAt);
        }

        public IEnumerable<Notification> GetAll()
        {
            return _notifications.Values.ToList();
        }
    }
}