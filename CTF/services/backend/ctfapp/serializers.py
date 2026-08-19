from rest_framework import serializers


class AuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class PingSerializer(serializers.Serializer):
    host = serializers.CharField(help_text="Host or IP to ping.")


class WebhookSerializer(serializers.Serializer):
    url = serializers.CharField(help_text="Target URL for the webhook test.")
    method = serializers.CharField(default="GET")
    headers = serializers.DictField(required=False)
