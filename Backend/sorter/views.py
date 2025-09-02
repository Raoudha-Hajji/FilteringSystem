from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
import mysql.connector
import json
from .filter import add_keyword, delete_keyword, re_filter

# Custom permissions
class IsStaffOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

# MySQL connection helper
def get_mysql_connection():
    from filterproject.db_utils import get_mysql_connection as get_db_connection
    return get_db_connection()

def get_filtered_table(request):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source
        FROM filtered_opp
        ORDER BY confidence DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return JsonResponse(rows, safe=False)

def get_rejected_table(request):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source
        FROM rejected_opp
        ORDER BY confidence DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return JsonResponse(rows, safe=False)

def get_keywords(request):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, keyword_fr FROM keywords ORDER BY id ASC")
    rows = cursor.fetchall()
    data = [{"id": row[0], "keyword_fr": row[1]} for row in rows]
    conn.close()
    return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def keyword_handler(request, keyword_id=None):
    if request.method == "GET":
        return get_keywords(request)

    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        if request.method == "POST":
            data = json.loads(request.body)
            keyword_fr = data.get("keyword_fr")
            if not keyword_fr:
                return JsonResponse({"error": "Missing 'keyword_fr'"}, status=400)
            add_keyword(keyword_fr)
            return JsonResponse({"success": True})

        elif request.method == "DELETE":
            if keyword_id is None:
                return JsonResponse({"error": "Keyword ID is required"}, status=400)
            delete_keyword(keyword_id)
            return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_POST
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refilter_handler(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({"error": "Permission denied"}, status=403)
    try:
        re_filter()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import mysql.connector
from filterproject.db_utils import get_mysql_connection

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_view(request):
    data = request.data
    required = ['consultation_id', 'client', 'intitule_projet', 'lien', 'Selection']
    if not all(k in data for k in required):
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 1. Save to training_data (for model training)
        cursor.execute("""
            INSERT INTO training_data (consultation_id, client, intitule_projet, lien, Selection)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['consultation_id'], data['client'], data['intitule_projet'], data['lien'], data['Selection']))
        
        # 2. MOVE ROWS BETWEEN TABLES based on Selection value
        if data['Selection'] == 1:  # Keep button clicked
            # Move row from rejected_opp → filtered_opp
            cursor.execute("""
                INSERT INTO filtered_opp (consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source)
                SELECT consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source
                FROM rejected_opp WHERE consultation_id = %s
            """, (data['consultation_id'],))
            
            # Remove from rejected_opp
            cursor.execute("DELETE FROM rejected_opp WHERE consultation_id = %s", (data['consultation_id'],))
            
        elif data['Selection'] == 0:  # Reject button clicked
            # Move row from filtered_opp → rejected_opp
            cursor.execute("""
                INSERT INTO rejected_opp (consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source)
                SELECT consultation_id, date_publication, client, intitule_projet, date_expiration, lien, source
                FROM filtered_opp WHERE consultation_id = %s
            """, (data['consultation_id'],))
            
            # Remove from filtered_opp
            cursor.execute("DELETE FROM filtered_opp WHERE consultation_id = %s", (data['consultation_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)