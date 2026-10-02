using System;

namespace SubscriptionService
{
    /// <summary>
    /// Represents a single subscription for a user.
    /// </summary>
    public class Subscription
    {
        public string UserId { get; set; } = string.Empty;
        public string PlanName { get; set; } = string.Empty;
        public DateTime StartedAt { get; set; }
        public DateTime? CancelledAt { get; private set; }

        public bool IsActive => CancelledAt == null;

        public void Cancel()
        {
            if (CancelledAt == null)
            {
                CancelledAt = DateTime.UtcNow;
            }
        }
    }
}