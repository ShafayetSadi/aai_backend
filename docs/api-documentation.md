# API Documentation

This document provides comprehensive information about the AAI Backend API endpoints.

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [User Management](#user-management)
- [Profile Management](#profile-management)
- [Location Management](#location-management)
- [Contact Management](#contact-management)
- [Job Management](#job-management)
- [Authentication Endpoints](#authentication-endpoints)
- [Response Formats](#response-formats)

## 🌐 Base URL

```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## 🔐 Authentication

All protected endpoints require authentication via JWT tokens.

### Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## ⚠️ Error Handling

### Standard Error Response

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 👥 User Management

### List Users

```http
GET /users/
```

**Query Parameters:**

- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 10, max: 100)
- `search` (string, optional): Search by username or email
- `is_active` (boolean, optional): Filter by active status

**Response:**

```json
{
  "users": [
    {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "is_active": true,
      "is_super_admin": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "last_login_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Get User

```http
GET /users/{user_id}
```

**Response:**

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true,
  "is_super_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T00:00:00Z"
}
```

### Create User

```http
POST /users/
```

**Request Body:**

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "is_active": true,
  "is_super_admin": false
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true,
  "is_super_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": null
}
```

### Update User

```http
PUT /users/{user_id}
```

**Request Body:**

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "is_active": true,
  "is_super_admin": false
}
```

**Response:**

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true,
  "is_super_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T00:00:00Z"
}
```

### Delete User (Soft Delete)

```http
DELETE /users/{user_id}
```

**Response:** `204 No Content`

### Activate User

```http
PATCH /users/{user_id}/activate
```

**Response:**

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "is_active": true,
  "is_super_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T00:00:00Z"
}
```

## 👤 Profile Management

### List Profiles

```http
GET /profiles/
```

**Query Parameters:**

- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 10, max: 100)
- `search` (string, optional): Search by name
- `is_public` (boolean, optional): Filter by public status

**Response:**

```json
{
  "profiles": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "first_name": "string",
      "last_name": "string",
      "date_of_birth": "2024-01-01",
      "gender": "male",
      "location_id": "uuid",
      "bio": "string",
      "profile_picture_url": "string",
      "is_public": true,
      "allow_contact": true,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "deactivated_at": null,
      "location": {
        "id": "uuid",
        "country": "USA",
        "state_province": "NY",
        "city": "New York",
        "postal_code": "10001"
      },
      "contacts": [
        {
          "id": "uuid",
          "type": "phone",
          "value": "+1234567890",
          "is_primary": true
        }
      ],
      "jobs": [
        {
          "id": "uuid",
          "title": "Software Engineer",
          "company": "Tech Corp",
          "industry": "Technology",
          "start_date": "2023-01-01",
          "end_date": null
        }
      ]
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Get Profile

```http
GET /profiles/{profile_id}
```

**Response:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "2024-01-01",
  "gender": "male",
  "location_id": "uuid",
  "bio": "string",
  "profile_picture_url": "string",
  "is_public": true,
  "allow_contact": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deactivated_at": null,
  "location": {
    "id": "uuid",
    "country": "USA",
    "state_province": "NY",
    "city": "New York",
    "postal_code": "10001"
  },
  "contacts": [
    {
      "id": "uuid",
      "type": "phone",
      "value": "+1234567890",
      "is_primary": true
    }
  ],
  "jobs": [
    {
      "id": "uuid",
      "title": "Software Engineer",
      "company": "Tech Corp",
      "industry": "Technology",
      "start_date": "2023-01-01",
      "end_date": null
    }
  ]
}
```

### Get Profile by User ID

```http
GET /profiles/user/{user_id}
```

**Response:** Same as Get Profile

### Get Profile with Full Relationships

```http
GET /profiles/{profile_id}/full
```

**Description:** Explicitly get a profile with all related data (location, contacts, jobs). This endpoint is optimized for loading relationships.

**Response:** Same as Get Profile

### Create Profile

```http
POST /profiles/
```

**Request Body:**

```json
{
  "user_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "2024-01-01",
  "gender": "male",
  "location_id": "uuid",
  "bio": "string",
  "profile_picture_url": "string",
  "is_public": true,
  "allow_contact": true
}
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "2024-01-01",
  "gender": "male",
  "location_id": "uuid",
  "bio": "string",
  "profile_picture_url": "string",
  "is_public": true,
  "allow_contact": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deactivated_at": null,
  "location": {
    "id": "uuid",
    "country": "USA",
    "state_province": "NY",
    "city": "New York",
    "postal_code": "10001"
  },
  "contacts": [],
  "jobs": []
}
```

### Update Profile

```http
PUT /profiles/{profile_id}
```

**Request Body:** Same as Create Profile (all fields optional)

**Response:** Same as Get Profile

### Delete Profile

```http
DELETE /profiles/{profile_id}
```

**Response:** `204 No Content`

### Update Profile Visibility

```http
PATCH /profiles/{profile_id}/visibility?is_public=true
```

**Query Parameters:**

- `is_public` (boolean): Set profile visibility

**Response:** Same as Get Profile

## 📍 Location Management

### List Locations

```http
GET /locations/
```

**Query Parameters:**

- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 10, max: 100)
- `search` (string, optional): Search by country or city

**Response:**

```json
{
  "locations": [
    {
      "id": "uuid",
      "country": "USA",
      "state_province": "NY",
      "city": "New York",
      "postal_code": "10001",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "deactivated_at": null
    }
  ],
  "total": 50,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

### Get Location

```http
GET /locations/{location_id}
```

**Response:**

```json
{
  "id": "uuid",
  "country": "USA",
  "state_province": "NY",
  "city": "New York",
  "postal_code": "10001",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deactivated_at": null
}
```

### Create Location

```http
POST /locations/
```

**Request Body:**

```json
{
  "country": "USA",
  "state_province": "NY",
  "city": "New York",
  "postal_code": "10001"
}
```

**Response:** `201 Created`

### Update Location

```http
PUT /locations/{location_id}
```

**Request Body:** Same as Create Location (all fields optional)

**Response:** Same as Get Location

### Delete Location

```http
DELETE /locations/{location_id}
```

**Response:** `204 No Content`

## 📞 Contact Management

### List Contacts

```http
GET /contacts/
```

**Query Parameters:**

- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 10, max: 100)
- `profile_id` (uuid, optional): Filter by profile ID
- `type` (string, optional): Filter by contact type

**Response:**

```json
{
  "contacts": [
    {
      "id": "uuid",
      "profile_id": "uuid",
      "type": "phone",
      "value": "+1234567890",
      "is_primary": true,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "deactivated_at": null
    }
  ],
  "total": 25,
  "page": 1,
  "size": 10,
  "pages": 3
}
```

### Get Contact

```http
GET /contacts/{contact_id}
```

**Response:**

```json
{
  "id": "uuid",
  "profile_id": "uuid",
  "type": "phone",
  "value": "+1234567890",
  "is_primary": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deactivated_at": null
}
```

### Create Contact

```http
POST /contacts/
```

**Request Body:**

```json
{
  "profile_id": "uuid",
  "type": "phone",
  "value": "+1234567890",
  "is_primary": true
}
```

**Response:** `201 Created`

### Update Contact

```http
PUT /contacts/{contact_id}
```

**Request Body:** Same as Create Contact (all fields optional)

**Response:** Same as Get Contact

### Delete Contact

```http
DELETE /contacts/{contact_id}
```

**Response:** `204 No Content`

## 💼 Job Management

### List Jobs

```http
GET /jobs/
```

**Query Parameters:**

- `page` (int, optional): Page number (default: 1)
- `size` (int, optional): Page size (default: 10, max: 100)
- `profile_id` (uuid, optional): Filter by profile ID
- `company` (string, optional): Filter by company
- `industry` (string, optional): Filter by industry

**Response:**

```json
{
  "jobs": [
    {
      "id": "uuid",
      "profile_id": "uuid",
      "title": "Software Engineer",
      "company": "Tech Corp",
      "industry": "Technology",
      "start_date": "2023-01-01",
      "end_date": null,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "deactivated_at": null
    }
  ],
  "total": 15,
  "page": 1,
  "size": 10,
  "pages": 2
}
```

### Get Job

```http
GET /jobs/{job_id}
```

**Response:**

```json
{
  "id": "uuid",
  "profile_id": "uuid",
  "title": "Software Engineer",
  "company": "Tech Corp",
  "industry": "Technology",
  "start_date": "2023-01-01",
  "end_date": null,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "deactivated_at": null
}
```

### Create Job

```http
POST /jobs/
```

**Request Body:**

```json
{
  "profile_id": "uuid",
  "title": "Software Engineer",
  "company": "Tech Corp",
  "industry": "Technology",
  "start_date": "2023-01-01",
  "end_date": null
}
```

**Response:** `201 Created`

### Update Job

```http
PUT /jobs/{job_id}
```

**Request Body:** Same as Create Job (all fields optional)

**Response:** Same as Get Job

### Delete Job

```http
DELETE /jobs/{job_id}
```

**Response:** `204 No Content`

## 🔑 Authentication Endpoints

### Register

```http
POST /auth/register
```

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "username"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### Login

```http
POST /auth/login
```

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### Refresh Token

```http
POST /auth/refresh
```

**Request Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /auth/me
```

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "is_super_admin": false
}
```

## 📊 Response Formats

### Pagination

All list endpoints support pagination with the following structure:

```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Gender Enum Values

- `male`
- `female`
- `other`
- `prefer_not_to_say`

## 🔗 Related Documentation

- [Database Migration Guide](./database-migrations.md)
- [Development Setup](./development-setup.md)
- [Architecture Overview](./architecture.md)

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
