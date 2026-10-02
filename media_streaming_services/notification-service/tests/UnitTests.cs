// =============================================================================
// UNIT TESTS for the Notification Service
// =============================================================================
// These tests exercise the notification service in isolation — no external
// systems, no network, no database. They run in milliseconds.
// =============================================================================

using System;
using Xunit;

namespace NotificationService.Tests
{
    /// <summary>
    /// Unit tests for the NotificationService class.
    /// </summary>
    public class UnitTests
    {
        /// <summary>
        /// A newly created notification should have IsSent == false
        /// until MarkAsSent is called.
        /// </summary>
        [Fact]
        public void NewNotification_IsNotSentByDefault()
        {
            // Arrange & Act
            var notification = new Notification
            {
                UserId = "user-1",
                Subject = "Welcome",
                Body = "Hello!",
            };

            // Assert
            Assert.False(notification.IsSent);
            Assert.Null(notification.SentAt);
        }

        /// <summary>
        /// Marking a notification as sent should set IsSent and SentAt.
        /// </summary>
        [Fact]
        public void MarkAsSent_SetsSentTimestamp()
        {
            // Arrange
            var notification = new Notification { UserId = "user-2" };

            // Act
            notification.MarkAsSent();

            // Assert
            Assert.True(notification.IsSent);
            Assert.NotNull(notification.SentAt);
        }

        /// <summary>
        /// Sending a notification via an unsupported channel should throw.
        /// </summary>
        [Fact]
        public void SendNotification_RejectsUnsupportedChannel()
        {
            // Arrange
            var service = new NotificationService(new InMemoryNotificationStore());

            // Act & Assert
            Assert.Throws<ArgumentException>(() =>
                service.SendNotification(
                    userId: "user-3",
                    channel: "carrier_pigeon",
                    subject: "Hi",
                    body: "Hi"));
        }

        /// <summary>
        /// Sending a notification with an empty user ID should throw.
        /// </summary>
        [Fact]
        public void SendNotification_RejectsEmptyUserId()
        {
            // Arrange
            var service = new NotificationService(new InMemoryNotificationStore());

            // Act & Assert
            Assert.Throws<ArgumentException>(() =>
                service.SendNotification(
                    userId: "",
                    channel: "email",
                    subject: "Hi",
                    body: "Hi"));
        }

        /// <summary>
        /// A fresh user should not have any notifications.
        /// </summary>
        [Fact]
        public void HasBeenNotified_ReturnsFalseForFreshUser()
        {
            // Arrange
            var service = new NotificationService(new InMemoryNotificationStore());

            // Act
            var result = service.HasBeenNotified("user-never-notified");

            // Assert
            Assert.False(result);
        }
    }
}