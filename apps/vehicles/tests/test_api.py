"""
Vehicle API Tests
Integration tests for vehicle REST endpoints
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.vehicles.infrastructure.models import Vehicle, VehicleCategory
from apps.vehicles.domain.entities import VehicleType, VehicleStatus


User = get_user_model()


class VehicleAPITestCase(APITestCase):
    """Test cases for Vehicle API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test category
        self.category = VehicleCategory.objects.create(
            name='Test Category',
            description='Test category for vehicles'
        )
        
        # Create test vehicles
        self.vehicle1 = Vehicle.objects.create(
            license_plate='ABC123',
            brand='Toyota',
            model='Camry',
            year=2020,
            vehicle_type=VehicleType.CAR.value,
            status=VehicleStatus.AVAILABLE.value,
            price=Decimal('25000.00'),
            mileage=15000,
            owner=self.user1,
            category=self.category,
            description='Test vehicle 1'
        )
        
        self.vehicle2 = Vehicle.objects.create(
            license_plate='XYZ789',
            brand='Ford',
            model='Transit',
            year=2019,
            vehicle_type=VehicleType.VAN.value,
            status=VehicleStatus.IN_USE.value,
            price=Decimal('35000.00'),
            mileage=25000,
            owner=self.user2,
            category=self.category,
            description='Test vehicle 2'
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user authentication"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_user(self, user):
        """Authenticate user for API requests"""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_list_vehicles_unauthenticated(self):
        """Test that unauthenticated users cannot list vehicles"""
        url = reverse('vehicles:vehicle-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_vehicles_authenticated(self):
        """Test listing vehicles for authenticated user"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # User should see their own vehicle and public ones
        self.assertTrue(len(response.data['results']) >= 1)
    
    def test_create_vehicle(self):
        """Test creating a new vehicle"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-list')
        
        data = {
            'license_plate': 'NEW123',
            'brand': 'Honda',
            'model': 'Civic',
            'year': 2021,
            'vehicle_type': VehicleType.CAR.value,
            'price': '20000.00',
            'mileage': 5000,
            'category': self.category.id,
            'description': 'New test vehicle'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['license_plate'], 'NEW123')
        self.assertEqual(response.data['owner'], self.user1.id)
    
    def test_retrieve_vehicle(self):
        """Test retrieving a specific vehicle"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': self.vehicle1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.vehicle1.id))
        self.assertEqual(response.data['license_plate'], 'ABC123')
    
    def test_update_own_vehicle(self):
        """Test updating own vehicle"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': self.vehicle1.id})
        
        data = {
            'brand': 'Toyota',
            'model': 'Camry Hybrid',
            'year': 2020,
            'vehicle_type': VehicleType.CAR.value,
            'price': '26000.00',
            'mileage': 16000,
            'category': self.category.id,
            'description': 'Updated test vehicle'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['model'], 'Camry Hybrid')
        self.assertEqual(response.data['price'], '26000.00')
    
    def test_update_other_user_vehicle_forbidden(self):
        """Test that users cannot update other users' vehicles"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': self.vehicle2.id})
        
        data = {
            'brand': 'Ford',
            'model': 'Transit Modified',
            'year': 2019,
            'vehicle_type': VehicleType.VAN.value,
            'price': '40000.00',
            'category': self.category.id
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_own_vehicle(self):
        """Test deleting own vehicle"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-detail', kwargs={'pk': self.vehicle1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vehicle should be soft deleted
        self.vehicle1.refresh_from_db()
        self.assertTrue(self.vehicle1.is_deleted)
    
    def test_vehicle_history(self):
        """Test getting vehicle history"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-history', kwargs={'pk': self.vehicle1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('vehicle_id', response.data)
        self.assertIn('history', response.data)
    
    def test_set_maintenance(self):
        """Test setting vehicle maintenance"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-set-maintenance', kwargs={'pk': self.vehicle1.id})
        
        data = {
            'maintenance_type': 'preventive',
            'description': 'Regular maintenance check',
            'scheduled_date': '2024-01-15T10:00:00Z'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_vehicle_statistics(self):
        """Test getting vehicle statistics"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain statistics about user's vehicles
    
    def test_search_vehicles(self):
        """Test vehicle search functionality"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-list')
        
        # Search by brand
        response = self.client.get(url, {'search': 'Toyota'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Search by license plate
        response = self.client.get(url, {'search': 'ABC123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_vehicles(self):
        """Test vehicle filtering"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-list')
        
        # Filter by vehicle type
        response = self.client.get(url, {'vehicle_type': VehicleType.CAR.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filter by status
        response = self.client.get(url, {'status': VehicleStatus.AVAILABLE.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filter by price range
        response = self.client.get(url, {'price__gte': '20000', 'price__lte': '30000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_see_all_vehicles(self):
        """Test that admin users can see all vehicles"""
        self.authenticate_user(self.admin_user)
        url = reverse('vehicles:vehicle-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin should see all vehicles
        self.assertTrue(len(response.data['results']) >= 2)
    
    def test_vehicle_validation(self):
        """Test vehicle data validation"""
        self.authenticate_user(self.user1)
        url = reverse('vehicles:vehicle-list')
        
        # Test invalid data
        invalid_data = {
            'license_plate': '',  # Required field
            'brand': 'Honda',
            'model': 'Civic',
            'year': 1800,  # Invalid year
            'vehicle_type': 'invalid_type',  # Invalid choice
            'price': '-1000.00',  # Negative price
            'category': self.category.id
        }
        
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VehicleModelTestCase(TestCase):
    """Test cases for Vehicle model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = VehicleCategory.objects.create(
            name='Test Category',
            description='Test category'
        )
    
    def test_create_vehicle(self):
        """Test creating a vehicle"""
        vehicle = Vehicle.objects.create(
            license_plate='TEST123',
            brand='Toyota',
            model='Prius',
            year=2020,
            vehicle_type=VehicleType.CAR.value,
            status=VehicleStatus.AVAILABLE.value,
            price=Decimal('30000.00'),
            mileage=0,
            owner=self.user,
            category=self.category
        )
        
        self.assertEqual(vehicle.license_plate, 'TEST123')
        self.assertEqual(vehicle.brand, 'Toyota')
        self.assertEqual(vehicle.owner, self.user)
        self.assertFalse(vehicle.is_deleted)
    
    def test_vehicle_str_representation(self):
        """Test vehicle string representation"""
        vehicle = Vehicle.objects.create(
            license_plate='TEST123',
            brand='Toyota',
            model='Prius',
            year=2020,
            vehicle_type=VehicleType.CAR.value,
            owner=self.user,
            category=self.category
        )
        
        expected_str = f'TEST123 - Toyota Prius (2020)'
        self.assertEqual(str(vehicle), expected_str)
    
    def test_soft_delete(self):
        """Test soft delete functionality"""
        vehicle = Vehicle.objects.create(
            license_plate='TEST123',
            brand='Toyota',
            model='Prius',
            year=2020,
            vehicle_type=VehicleType.CAR.value,
            owner=self.user,
            category=self.category
        )
        
        # Soft delete
        vehicle.soft_delete()
        
        self.assertTrue(vehicle.is_deleted)
        self.assertIsNotNone(vehicle.deleted_at)
        
        # Vehicle should not appear in default queryset
        self.assertFalse(Vehicle.objects.filter(id=vehicle.id).exists())
        
        # But should appear in all_objects queryset
        self.assertTrue(Vehicle.all_objects.filter(id=vehicle.id).exists())
