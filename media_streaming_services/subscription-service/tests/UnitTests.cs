// =============================================================================
// UNIT TESTS for the Subscription Service
// =============================================================================
// These tests verify individual units of logic in the subscription service
// without touching external dependencies. They run fast and are pure.
// =============================================================================

using System;
using Xunit;

namespace SubscriptionService.Tests
{
    /// <summary>
    /// Unit tests for the subscription service.
    /// Each test exercises one small piece of business logic.
    /// </summary>
    public class UnitTests
    {
        /// <summary>
        /// Verifies that a new subscription has the expected default values.
        /// </summary>
        [Fact]
        public void NewSubscription_HasActiveStatus()
        {
            // Arrange & Act
            var subscription = new Subscription
            {
                UserId = "user-123",
                PlanName = "Basic",
                StartedAt = DateTime.UtcNow,
            };

            // Assert
            Assert.NotNull(subscription);
            Assert.Equal("user-123", subscription.UserId);
            Assert.Equal("Basic", subscription.PlanName);
            Assert.True(subscription.IsActive);
        }

        /// <summary>
        /// Verifies that cancelling a subscription flips its active flag.
        /// </summary>
        [Fact]
        public void Cancel_ChangesStatusToInactive()
        {
            // Arrange
            var subscription = new Subscription
            {
                UserId = "user-456",
                PlanName = "Premium",
                StartedAt = DateTime.UtcNow,
            };

            // Act
            subscription.Cancel();

            // Assert
            Assert.False(subscription.IsActive);
            Assert.NotNull(subscription.CancelledAt);
        }

        /// <summary>
        /// Verifies that an unknown user does not have a subscription.
        /// </summary>
        [Fact]
        public void UnknownUser_HasNoSubscription()
        {
            // Arrange
            var service = new SubscriptionService(new InMemorySubscriptionStore());
            const string unknownUserId = "user-does-not-exist";

            // Act
            var result = service.GetSubscription(unknownUserId);

            // Assert
            Assert.Null(result);
        }

        /// <summary>
        /// Verifies that creating a subscription stores it in the backend.
        /// </summary>
        [Fact]
        public void CreateSubscription_StoresItInTheBackend()
        {
            // Arrange
            var store = new InMemorySubscriptionStore();
            var service = new SubscriptionService(store);

            // Act
            var created = service.CreateSubscription("user-789", "Basic");
            var retrieved = store.Get("user-789");

            // Assert
            Assert.NotNull(created);
            Assert.NotNull(retrieved);
            Assert.Equal(created.UserId, retrieved.UserId);
            Assert.Equal("Basic", retrieved.PlanName);
        }

        /// <summary>
        /// Verifies that the plan validation rejects unknown plan names.
        /// </summary>
        [Fact]
        public void CreateSubscription_RejectsUnknownPlan()
        {
            // Arrange
            var service = new SubscriptionService(new InMemorySubscriptionStore());

            // Act & Assert
            Assert.Throws<ArgumentException>(() =>
                service.CreateSubscription("user-999", "UnknownPlan"));
        }
    }
}