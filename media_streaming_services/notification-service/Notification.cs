// =============================================================================
// NOTIFICATION model
// =============================================================================
// Represents a single notification sent to a user.
// =============================================================================

using System;

namespace NotificationService
{
    /// <summary>
    /// Represents one notification that was or will be sent to a user.
    /// </summary>
    public class Notification
    {
        public string NotificationId { get; set; } = Guid.NewGuid().ToString();
        public string UserId { get; set; } = string.Empty;
        public string Channel { get; set; } = "email";  // email | sms | push
        public string Subject { get; set; } = string.Empty;
        public string Body { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? SentAt { get; private set; }

        public bool IsSent => SentAt != null;

        public void MarkAsSent()
        {
            if (SentAt == null)
            {
                SentAt = DateTime.UtcNow;
            }
        }
    }
}