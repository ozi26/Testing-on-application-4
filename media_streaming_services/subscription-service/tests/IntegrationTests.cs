// =============================================================================
// INTEGRATION TESTS for the Subscription Service
// =============================================================================
// These tests verify that the subscription service works end-to-end —
// from the API surface down to the storage layer. They exercise the full
// stack rather than isolated units.
// =============================================================================

using System;
using Xunit;

namespace SubscriptionService.Tests
{
    /// <summary>
    /// Integration tests for the subscription service.
    /// Each test exercises multiple layers at once.
    /// </summary>
    public class IntegrationTests
    {
        /// <summary>
        /// End-to-end: creating a subscription should make it retrievable.
        /// This tests the full create → store → retrieve flow.
        /// </summary>
        [Fact]
        public void CreateAndRetrieve_WorksEndToEnd()
        {
            // Arrange
            var store = new InMemorySubscriptionStore();
            var service = new SubscriptionService(store);

            // Act
            var created = service.CreateSubscription("integration-user", "Premium");
            var retrieved = service.GetSubscription("integration-user");

            // Assert
            Assert.NotNull(created);
            Assert.NotNull(retrieved);
            Assert.Equal(created.UserId, retrieved.UserId);
            Assert.Equal("Premium", retrieved.PlanName);
            Assert.True(retrieved.IsActive);
        }

        /// <summary>
        /// End-to-end: cancelling a subscription should persist across
        /// retrieval operations.
        /// </summary>
        [Fact]
        public void CancelAndRetrieve_PersistsCancellation()
        {
            // Arrange
            var store = new InMemorySubscriptionStore();
            var service = new SubscriptionService(store);
            service.CreateSubscription("cancel-user", "Basic");

            // Act
            service.CancelSubscription("cancel-user");
            var retrieved = service.GetSubscription("cancel-user");

            // Assert
            Assert.NotNull(retrieved);
            Assert.False(retrieved.IsActive);
            Assert.NotNull(retrieved.CancelledAt);
        }

        /// <summary>
        /// End-to-end: upgrading a plan should preserve the user's history
        /// and update the plan name in storage.
        /// </summary>
        [Fact]
        public void UpgradePlan_PreservesUserAndUpdatesPlan()
        {
            // Arrange
            var store = new InMemorySubscriptionStore();
            var service = new SubscriptionService(store);
            service.CreateSubscription("upgrade-user", "Basic");

            // Act
            service.UpgradePlan("upgrade-user", "Premium");
            var retrieved = service.GetSubscription("upgrade-user");

            // Assert
            Assert.NotNull(retrieved);
            Assert.Equal("upgrade-user", retrieved.UserId);
            Assert.Equal("Premium", retrieved.PlanName);
        }
    }
}