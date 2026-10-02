using System.Collections.Generic;

namespace SubscriptionService
{
    /// <summary>
    /// Simple in-memory subscription store used for testing and demos.
    /// </summary>
    public class InMemorySubscriptionStore
    {
        private readonly Dictionary<string, Subscription> _subscriptions = new();

        public void Save(Subscription subscription)
        {
            _subscriptions[subscription.UserId] = subscription;
        }

        public Subscription? Get(string userId)
        {
            return _subscriptions.TryGetValue(userId, out var sub) ? sub : null;
        }
    }
}