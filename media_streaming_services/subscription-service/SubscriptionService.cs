using System;
using System.Collections.Generic;

namespace SubscriptionService
{
    /// <summary>
    /// The main subscription business logic.
    /// </summary>
    public class SubscriptionService
    {
        private static readonly HashSet<string> KnownPlans = new()
        {
            "Basic", "Premium", "Enterprise",
        };

        private readonly InMemorySubscriptionStore _store;

        public SubscriptionService(InMemorySubscriptionStore store)
        {
            _store = store ?? throw new ArgumentNullException(nameof(store));
        }

        public Subscription CreateSubscription(string userId, string planName)
        {
            if (!KnownPlans.Contains(planName))
            {
                throw new ArgumentException($"Unknown plan: {planName}");
            }

            var subscription = new Subscription
            {
                UserId = userId,
                PlanName = planName,
                StartedAt = DateTime.UtcNow,
            };

            _store.Save(subscription);
            return subscription;
        }

        public Subscription? GetSubscription(string userId)
        {
            return _store.Get(userId);
        }

        public void CancelSubscription(string userId)
        {
            var sub = _store.Get(userId);
            if (sub == null)
            {
                throw new InvalidOperationException(
                    $"No subscription found for user: {userId}");
            }
            sub.Cancel();
            _store.Save(sub);
        }

        public void UpgradePlan(string userId, string newPlanName)
        {
            if (!KnownPlans.Contains(newPlanName))
            {
                throw new ArgumentException($"Unknown plan: {newPlanName}");
            }

            var sub = _store.Get(userId);
            if (sub == null)
            {
                throw new InvalidOperationException(
                    $"No subscription found for user: {userId}");
            }

            sub.PlanName = newPlanName;
            _store.Save(sub);
        }
    }
}