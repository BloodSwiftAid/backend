from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..serializers.public_serializers import FacilityRegistrationSerializer, PotentialDonorSerializer

class RegisterFacilityView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = FacilityRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Facility registration submitted successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterDonorView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PotentialDonorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Donor registration submitted successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
