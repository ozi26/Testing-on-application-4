// =============================================================================
// INTEGRATION TESTS for the Notification Service
// =============================================================================
// These tests verify the full send → store → retrieve flow.
// =============================================================================

using System;
using System.Linq;
using Xunit;

namespace NotificationService.Tests
{
    /// <summary>
    /// Integration tests for the notification service.
    /// </summary>
    public class IntegrationTests
    {
        /// <summary>
        /// End-to-end: sending a notification should make it retrievable
        /// by ID.
        /// </summary>
        [Fact]
        public void SendAndRetrieve_WorksEndToEnd()
        {
            // Arrange
            var store = new InMemoryNotificationStore();
            var service = new NotificationService(store);

            // Act
            var sent = service.SendNotification(
                userId: "integration-user",
                channel: "email",
                subject: "Welcome",
                body: "Thanks for signing up!");

            var retrieved = service.GetNotification(sent.NotificationId);

            // Assert
            Assert.NotNull(retrieved);
            Assert.Equal(sent.NotificationId, retrieved!.NotificationId);
            Assert.Equal("integration-user", retrieved.UserId);
            Assert.True(retrieved.IsSent);
        }

        /// <summary>
        /// A user with multiple notifications should get them all back,
        /// newest first.
        /// </summary>
        [Fact]
        public void MultipleNotifications_AllReturnedForUser()
        {
            // Arrange
            var service = new NotificationService(new InMemoryNotificationStore());

            // Act
            service.SendNotification("multi-user", "email", "First", "One");
            service.SendNotification("multi-user", "sms", "Second", "Two");
            service.SendNotification("multi-user", "push", "Third", "Three");

            var notifications = service.GetUserNotifications("multi-user").ToList();

            // Assert
            Assert.Equal(3, notifications.Count);
            Assert.All(notifications, n => Assert.Equal("multi-user", n.UserId));
        }

        /// <summary>
        /// After sending a notification, HasBeenNotified should return true.
        /// </summary>
        [Fact]
        public void AfterSending_HasBeenNotifiedReturnsTrue()
        {
            // Arrange
            var service = new NotificationService(new InMemoryNotificationStore());

            // Act
            service.SendNotification("notified-user", "email", "Hello", "World");
            var result = service.HasBeenNotified("notified-user");

            // Assert
            Assert.True(result);
        }
    }
}