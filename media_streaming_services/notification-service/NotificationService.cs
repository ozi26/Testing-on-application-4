// =============================================================================
// NOTIFICATION BUSINESS LOGIC
// =============================================================================
// Sends notifications to users via email, SMS, or push channels.
// This is the class exercised by the unit and integration tests.
// =============================================================================

using System;
using System.Collections.Generic;

namespace NotificationService
{
    /// <summary>
    /// Main business logic for sending notifications.
    /// </summary>
    public class NotificationService
    {
        private static readonly HashSet<string> SupportedChannels = new()
        {
            "email", "sms", "push",
        };

        private readonly InMemoryNotificationStore _store;

        public NotificationService(InMemoryNotificationStore store)
        {
            _store = store ?? throw new ArgumentNullException(nameof(store));
        }

        /// <summary>
        /// Creates and sends a notification to the given user.
        /// </summary>
        public Notification SendNotification(
            string userId,
            string channel,
            string subject,
            string body)
        {
            if (string.IsNullOrWhiteSpace(userId))
            {
                throw new ArgumentException("userId is required");
            }
            if (!SupportedChannels.Contains(channel))
            {
                throw new ArgumentException($"Unsupported channel: {channel}");
            }

            var notification = new Notification
            {
                UserId = userId,
                Channel = channel,
                Subject = subject,
                Body = body,
            };

            // Simulate sending
            notification.MarkAsSent();

            _store.Save(notification);
            return notification;
        }

        /// <summary>
        /// Retrieves a notification by its ID.
        /// </summary>
        public Notification? GetNotification(string notificationId)
        {
            return _store.Get(notificationId);
        }

        /// <summary>
        /// Lists all notifications for a given user, newest first.
        /// </summary>
        public IEnumerable<Notification> GetUserNotifications(string userId)
        {
            return _store.GetByUser(userId);
        }

        /// <summary>
        /// Returns true if at least one notification was sent to the user.
        /// </summary>
        public bool HasBeenNotified(string userId)
        {
            foreach (var _ in _store.GetByUser(userId))
            {
                return true;
            }
            return false;
        }
    }
}