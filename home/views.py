import datetime
import os
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
import smtplib
from pymysql import OperationalError, InterfaceError
from django.core.mail import send_mail
import logging
from django.views.decorators.cache import never_cache

from .utils import sendsms  
import pymysql
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render,get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
import uuid
from django.urls import reverse
from django.db import  transaction
from django.core.exceptions import ValidationError
import re
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection
from django.db import connection
from django.views.decorators.http import require_POST
import json
now = datetime.datetime.now()
conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
c = conn.cursor()

def index(request):
    return render(request,'index.html')


from django.contrib.auth.hashers import make_password, check_password

#------------------------user registration------------------------------------------
from django.contrib.auth.hashers import make_password

#------------------------user registration------------------------------------------
def register(request):
    data = {}  

    if request.method == 'POST':
        user_type = request.POST.get('userType')
        myfile = request.FILES["img"]
        id_proof_file = request.FILES["idProofFile"]

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        
        id_proof_fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        id_proof_filename = id_proof_fs.save(id_proof_file.name, id_proof_file)
        id_proof_uploaded_file_url = id_proof_fs.url(id_proof_filename)

        common_data = {
            "name": request.POST.get("name"),
            "age": request.POST.get("age"),
            "gender": request.POST.get("gender"),
            "email": request.POST.get("email"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "password": make_password(request.POST.get("password")),  # Hash the password
            "state": request.POST.get("state"),
            "district": request.POST.get("district"),
            "id_proof_type": request.POST.get("idProofType"),
            "id_proof_url": id_proof_uploaded_file_url,
            "pincode": request.POST.get("pincode"),
        }

        if user_type == 'advocate':
            advocate_data = {
                "enrollment_number": request.POST.get("enrollmentNumber"),
                "qualification1": request.POST.get("qualifications1"),
                "qualification2": request.POST.get("qualifications2"),
            }
            return register_advocate(request, common_data, advocate_data, uploaded_file_url, data)
        else:
            return register_client(request, common_data, uploaded_file_url, data)

    return render(request, "register.html", {"data": data})

def register_advocate(request, common_data, advocate_data, uploaded_file_url, data):
    # Check in tbl_user for existing email or phone
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        # Insert into tbl_user
        s2 = """INSERT INTO tbl_user (u_img, u_name, gender, age, email, phone, address, 
        state, district, pincode, id_proof_type, id_proof_url, password, u_type, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'advocate', 0)"""

        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        
        # Insert into tbl_advocate
        s3 = """INSERT INTO tbl_advocate (Entrollmentno, adv_qualification1, adv_qualification2, u_id, status) 
        VALUES (%s, %s, %s, %s,  0)"""
        qualifications = ', '.join([advocate_data['qualification1'], advocate_data['qualification2']])
        
        c.execute(s3, (advocate_data['enrollment_number'], advocate_data['qualification1'], advocate_data['qualification2'], user_id))
        conn.commit()

        msg = "Advocate Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html", data)
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html",  data)

def register_client(request, common_data, uploaded_file_url, data):
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        s2 = """INSERT INTO tbl_user (u_img, u_name,gender,age,email,phone,address, 
                state, district, pincode,id_proof_type, id_proof_url,password,u_type, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s,'client', 1)"""
        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        s3 = "INSERT INTO tbl_client (u_id, status) VALUES (%s, 1)"
        c.execute(s3, (user_id,))
        conn.commit()

        msg = "Client Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html",  data)
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html",  data)

#---------------------------------------- login-------------------------------------------------------------
#---------------------------------------- login-------------------------------------------------------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        s1 = "SELECT * FROM tbl_user WHERE email = %s"
        c.execute(s1, (email,))
        user_details = c.fetchone()

        if not user_details:
            msg = "User Does Not Exist"
            return render(request, "login.html", {"msg": msg})

        hashed_password = user_details[15]  # Password is at index 15
        u_id = user_details[0]  # ID is at index 0
        u_type = user_details[16]  # User type is at index 16
        status = user_details[17]  # Status is at index 17

        if not check_password(password, hashed_password):
            msg = "Incorrect Password"
            return render(request, "login.html", {"msg": msg})

        if status != 1:
            msg = "Your account is not activated"
            return render(request, "login.html", {"msg": msg})

        if u_type == 'admin':
            request.session["admin_id"] = u_id
            return HttpResponseRedirect("/admin_home")
        elif u_type == 'advocate':
            # Check if advocate has selected a category
            s2 = "SELECT category FROM tbl_advocate WHERE u_id = %s"
            c.execute(s2, (u_id,))
            cat_id = c.fetchone()[0]
            
            request.session["adv_id"] = u_id
            
            if not cat_id:
                return HttpResponseRedirect("/adv_home/select_category")
            
            return HttpResponseRedirect("/adv_home")
        elif u_type == 'client':
            request.session["client_id"] = u_id
            return HttpResponseRedirect("/client_home")

        msg = "Invalid user type or credentials"
        return render(request, "login.html", {"msg": msg})

    return render(request, "login.html")
#------------------------------select category----------------------------------
def select_category(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")
    
    adv_id = request.session.get("adv_id")
    
    if request.method == 'POST':
        category_id = request.POST.get("category_id")
        
        # Update the selected category in the database
        s3 = "UPDATE tbl_advocate SET category = %s WHERE u_id = %s"
        c.execute(s3, (category_id, adv_id))
        conn.commit()
        
        return HttpResponseRedirect("/adv_home")
    
    # Fetch available categories from the database
    with conn.cursor() as cursor:
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    # Render the select_category.html template with the list of categories
    return render(request, "advocate/select_category.html", {"categories": categories})
#---------------------------Logout----------------------------------------------#
def logout(request):
    request.session.flush()
    return redirect("login")
#--------------------------forgot password--------------------------------------
#--------------------------password-reset---------------------------------------
def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_user WHERE email = %s", [email])
            user = cursor.fetchone()
            
            if user:
                token = str(uuid.uuid4())
                reset_url = f'http://127.0.0.1:8000/reset/{token}/'
                subject = 'Password Reset'
                message = f'Click the following link to reset your password: {reset_url}'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [email]
                
                email_message = EmailMultiAlternatives(subject, message, from_email, to_email)
                email_message.send()
                
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO password_reset (user_email, token) VALUES (%s, %s)", [email, token])
                    conn.commit()
                msg="Password reset link has been sent to your mail. Kindly check your mail and follow the procedures"
                return render(request, "login.html", {"msg": msg})

            else:
                msg="User with this email does not exist"
                return render(request, "login.html", {"msg": msg})
    return render(request, 'login.html')
#--------------------------------password-confirmation-------------------------------------------------------------------
def password_reset_confirm(request, token):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_email FROM password_reset WHERE token = %s", [token])
                result = cursor.fetchone()
                
                if result:
                    email = result[0]
                    cursor.execute("SELECT u_id FROM tbl_user WHERE email = %s", [email])
                    user_id = cursor.fetchone()
                    
                    if user_id:
                        user_id = user_id[0]
                        hashed_password = make_password(new_password)  # Hashing the new password
                        cursor.execute("UPDATE tbl_user SET password = %s WHERE u_id = %s", [hashed_password, user_id])
                        conn.commit()

                        cursor.execute("DELETE FROM password_reset WHERE token = %s", [token])
                        conn.commit()

                        return redirect('login')
                return render(request, 'password_reset_confirm.html', {'error': 'Invalid or expired token', 'token': token})
        else:
            return render(request, 'password_reset_confirm.html', {'error': 'Passwords do not match', 'token': token})

    return render(request, 'password_reset_confirm.html', {'token': token})
#---------------------------------password-confirmation-end---------------------------------------------

#----------------------------------------Admin-----------------------------------#
def admin_home(request):
    
    if "admin_id" not in request.session:
        return redirect("login")
    response = render(request, 'admin/admin_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
#--------------------------------------Advocate-request-----------------------------
def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    response = render(request, 'admin/admin_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    response = render(request, 'admin/admin_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
    try:
        s1 = """
        SELECT a.Entrollmentno, u.u_name, u.u_img, u.age, u.email, u.phone, a.adv_qualification1,
               a.adv_qualification2, u.state, u.district, u.pincode, u.id_proof_type, u.id_proof_url, u.u_id
        FROM tbl_advocate a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'advocate'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/adv_req.html", {"msgg": msg})
        
        # Convert the fetched data into a list of dictionaries
        data_list = []
        for row in data:
            data_list.append({
                "Entrollmentno": row[0],
                "u_name": row[1],
                "u_img": row[2].replace('/media/', ''),
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "adv_qualification1": row[6],
                "adv_qualification2": row[7],
                "state": row[8],
                "district": row[9],
                "pincode": row[10],
                "id_proof_type": row[11],
                "id_proof_url": row[12],
                "u_id": row[13]
            })

        print("Data List:", data_list)  # Debug print for data list
        
        return render(request, "admin/adv_req.html", {"data": data_list, "MEDIA_URL": settings.MEDIA_URL})

    except Exception as e:
        print("Exception occurred:", e)  # Print the exception
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})

def action_adv(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='1' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()

            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='2' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()
            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

    except Exception as e:
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})
#---------------------client request----------------------------------------------------------->
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    return render(request,'admin/client_req.html')
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        s1 = """
        SELECT a.c_id, u.u_name,u.u_img, u.age, u.email, u.phone,  u.state, u.district, u.pincode, u.u_id
        FROM tbl_client a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'client'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/client_req.html", {"msgg": msg})
        
        data_list = []
        for row in data:
            data_list.append({
                "c_id": row[0],
                "u_name": row[1],
                "u_img": row[2],
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "state": row[6],
                "district": row[7],
                "pincode": row[8],
                "u_id": row[9]
            })
        
        return render(request, "admin/client_req.html", {"data": data_list})

    except Exception as e:
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})


def action_client(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='1' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Approve):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='2' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Reject):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

    except Exception as e:
        print("Exception occurred:", e)  
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})
#--------------------------------------- User list ----------------------------------------------------------
#----------------------------------------advocate list-------------------------------------------------------
def approved_advocates_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, a.Entrollmentno, u.u_img, u.age, 
                   a.adv_qualification1, a.adv_qualification2, u.pincode, 
                   u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_type = 'advocate' AND u.status = 1 AND a.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    advocates = []
    for row in rows:
        is_pdf = row[13].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 13
        advocate_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'Entrollmentno': row[6],
            'u_img': row[7],
            'age': row[8],
            'adv_qualification1': row[9],
            'adv_qualification2': row[10],
            'pincode': row[11],
            'id_proof_type': row[12],
            'id_proof_url': row[13],
            'is_pdf': is_pdf
        }
        advocates.append(advocate_data)

    return render(request, 'admin/approved_advocate_list.html', {'advocates': advocates})
#----------------------------------------client list --------------------------------------------------------

def client_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, u.u_img, u.age, 
                   u.pincode, u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            WHERE u.u_type = 'client' AND u.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    clients = []
    for row in rows:
        is_pdf = row[10].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 10
        client_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'u_img': row[6],
            'age': row[7],
            'pincode': row[8],
            'id_proof_type': row[9],
            'id_proof_url': row[10],
            'is_pdf': is_pdf
        }
        clients.append(client_data)

    return render(request, 'admin/client_list.html', {'clients': clients})

#----------------------------------delete advocate------------------------------------------------------------
def delete_advocate(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the advocate to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'advocate'", [u_id])
        cursor.execute("UPDATE tbl_advocate SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the approved advocates list
    return HttpResponseRedirect('/admin_home/approved_advocates/')
#----------------------------------delete client---------------------------------------------------------------
def delete_client(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the client to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'client'", [u_id])
        cursor.execute("UPDATE tbl_client SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the client list
    return HttpResponseRedirect('/admin_home/client_list/')
#---------------------------------advocate---------------------------------------------------------
def adv_home(request):
    if "adv_id" not in request.session:
        return redirect("login")
    response = render(request, 'advocate/adv_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

#-------------------------------advocate profile view -------------------------------------------------------
def advocate_profile(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")

    adv_id = request.session.get("adv_id")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.u_img, u.u_name, u.gender, u.age, u.email, u.phone, 
                u.address, u.state, u.district, u.pincode, 
                u.id_proof_type, u.id_proof_url, 
                a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [adv_id])
        
        advocate_details = cursor.fetchone()
    
    if advocate_details:
        data = {
            "img_url": advocate_details[0],
            "name": advocate_details[1],
            "gender": advocate_details[2],
            "age": advocate_details[3],
            "email": advocate_details[4],
            "phone": advocate_details[5],
            "address": advocate_details[6],
            "state": advocate_details[7],
            "district": advocate_details[8],
            "pincode": advocate_details[9],
            "id_proof_type": advocate_details[10],
            "id_proof_url": advocate_details[11],
            "enrollment_number": advocate_details[12],
            "qualification1": advocate_details[13],
            "qualification2": advocate_details[14],
        }
    else:
        data = {"msg": "Profile not found"}

    return render(request, "advocate/advocate_profile.html", {"data": data})
#---------------------------------------advocate prfile update-----------------------------------------------
def advocate_profile_update(request):
    data = {}

    # Ensure the user is logged in
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    user_id = request.session['adv_id']

    if request.method == 'POST':
        # Get the profile data from the form
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        pincode = request.POST.get("pincode")
        taluk = request.POST.get("taluk")
        village = request.POST.get("village")
        id_proof_type = request.POST.get("idProofType")
        id_proof_file = request.FILES.get("idProofFile")
        img = request.FILES.get("img")
        enrollment_number = request.POST.get("enrollmentNumber")
        qualification1 = request.POST.get("qualifications1")
        qualification2 = request.POST.get("qualifications2")

        with conn.cursor() as cursor:
            # Check if email or phone is being updated to an existing user's email or phone
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_user 
                WHERE (email = %s OR phone = %s) 
                AND u_id != %s
            """, [email, phone, user_id])
            count = cursor.fetchone()[0]

            if count == 0:
                # Update profile image if a new one is uploaded
                if img:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    img_filename = fs.save(img.name, img)
                    img_url = fs.url(img_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET u_img = %s 
                        WHERE u_id = %s
                    """, [img_url, user_id])

                # Update ID proof if a new one is uploaded
                if id_proof_file:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    id_proof_filename = fs.save(id_proof_file.name, id_proof_file)
                    id_proof_url = fs.url(id_proof_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET id_proof_url = %s 
                        WHERE u_id = %s
                    """, [id_proof_url, user_id])

                # Update the rest of the profile information in tbl_user
                cursor.execute("""
                    UPDATE tbl_user 
                    SET u_name = %s, age = %s, gender = %s, email = %s, phone = %s, address = %s, state = %s, district = %s, pincode = %s, taluk = %s, village = %s, id_proof_type = %s
                    WHERE u_id = %s
                """, [name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, user_id])

                # Update advocate-specific information in tbl_advocate
                cursor.execute("""
                    UPDATE tbl_advocate 
                    SET Entrollmentno = %s, adv_qualification1 = %s, adv_qualification2 = %s
                    WHERE u_id = %s
                """, [enrollment_number, qualification1, qualification2, user_id])

                # Commit the transaction
                conn.commit()

                # Update session data if needed
                request.session['adv_name'] = name
                request.session['adv_email'] = email
                request.session['adv_phone'] = phone

                data["msg"] = "Profile updated successfully."
            else:
                data["msg"] = "Email or phone already exists."

    # Fetch current profile data
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_img, u.u_name, u.age, u.gender, u.email, u.phone, u.address, u.state, u.district, u.pincode, u.taluk, u.village, u.id_proof_type, u.id_proof_url,
                   a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [user_id])
        user_details = cursor.fetchone()

    if not user_details:
        data["msg"] = "Profile not found."
    else:
        profile_data = {
            "u_img": user_details[0],
            "name": user_details[1],
            "age": user_details[2],
            "gender": user_details[3],
            "email": user_details[4],
            "phone": user_details[5],
            "address": user_details[6],
            "state": user_details[7],
            "district": user_details[8],
            "pincode": user_details[9],
            "taluk": user_details[10],
            "village": user_details[11],
            "id_proof_type": user_details[12],
            "id_proof_url": user_details[13],
            "enrollment_number": user_details[14],
            "qualification1": user_details[15],
            "qualification2": user_details[16],
        }
        data["profile"] = profile_data

    return render(request, "advocate/advocate_profile_update.html", {"data": data})

#--------------------------------change password-------------------------------------------------------
import datetime
import os
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
import smtplib
from .utils import sendsms  
import pymysql
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
import uuid
from django.urls import reverse
from django.db import  transaction
from django.core.exceptions import ValidationError
import re
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

now = datetime.datetime.now()
conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
c = conn.cursor()

def index(request):
    return render(request,'index.html')


from django.contrib.auth.hashers import make_password, check_password

#------------------------user registration------------------------------------------
from django.contrib.auth.hashers import make_password

#------------------------user registration------------------------------------------
def register(request):
    data = {}  

    if request.method == 'POST':
        user_type = request.POST.get('userType')
        myfile = request.FILES["img"]
        id_proof_file = request.FILES["idProofFile"]

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        
        id_proof_fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
        id_proof_filename = id_proof_fs.save(id_proof_file.name, id_proof_file)
        id_proof_uploaded_file_url = id_proof_fs.url(id_proof_filename)

        common_data = {
            "name": request.POST.get("name"),
            "age": request.POST.get("age"),
            "gender": request.POST.get("gender"),
            "email": request.POST.get("email"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "password": make_password(request.POST.get("password")),  # Hash the password
            "state": request.POST.get("state"),
            "district": request.POST.get("district"),
            "id_proof_type": request.POST.get("idProofType"),
            "id_proof_url": id_proof_uploaded_file_url,
            "pincode": request.POST.get("pincode"),
        }

        if user_type == 'advocate':
            advocate_data = {
                "enrollment_number": request.POST.get("enrollmentNumber"),
                "qualification1": request.POST.get("qualifications1"),
                "qualification2": request.POST.get("qualifications2"),
            }
            return register_advocate(request, common_data, advocate_data, uploaded_file_url, data)
        else:
            return register_client(request, common_data, uploaded_file_url, data)

    return render(request, "register.html", {"data": data})

def register_advocate(request, common_data, advocate_data, uploaded_file_url, data):
    # Check in tbl_user for existing email or phone
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        # Insert into tbl_user
        s2 = """INSERT INTO tbl_user (u_img, u_name, gender, age, email, phone, address, 
        state, district, pincode, id_proof_type, id_proof_url, password, u_type, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'advocate', 0)"""

        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        
        # Insert into tbl_advocate
        s3 = """INSERT INTO tbl_advocate (Entrollmentno, adv_qualification1, adv_qualification2, u_id, status) 
        VALUES (%s, %s, %s, %s,  0)"""
        qualifications = ', '.join([advocate_data['qualification1'], advocate_data['qualification2']])
        
        c.execute(s3, (advocate_data['enrollment_number'], advocate_data['qualification1'], advocate_data['qualification2'], user_id))
        conn.commit()

        msg = "Advocate Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html", data)
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html",  data)

def register_client(request, common_data, uploaded_file_url, data):
    s1 = "SELECT COUNT(*) FROM tbl_user WHERE email = %s OR phone = %s"
    c.execute(s1, (common_data['email'], common_data['phone']))
    reg_count = c.fetchone()

    if reg_count[0] == 0:
        s2 = """INSERT INTO tbl_user (u_img, u_name,gender,age,email,phone,address, 
                state, district, pincode,id_proof_type, id_proof_url,password,u_type, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s,'client', 1)"""
        c.execute(s2, (uploaded_file_url, common_data['name'], common_data['gender'], common_data['age'], 
                       common_data['email'], common_data['phone'], common_data['address'], common_data['state'], 
                       common_data['district'], common_data['pincode'], common_data['id_proof_type'], common_data['id_proof_url'], 
                       common_data['password']))
        conn.commit()

        user_id = c.lastrowid
        s3 = "INSERT INTO tbl_client (u_id, status) VALUES (%s, 1)"
        c.execute(s3, (user_id,))
        conn.commit()

        msg = "Client Registered Successfully, Your Account will be activated soon."
        data["msg"] = msg
        return render(request, "register.html",  data)
    else:
        msg = "Account Already Exists"
        data["msg"] = msg
        return render(request, "register.html",  data)

#---------------------------------------- login-------------------------------------------------------------
#---------------------------------------- login-------------------------------------------------------------
def login(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        s1 = "SELECT * FROM tbl_user WHERE email = %s"
        c.execute(s1, (email,))
        user_details = c.fetchone()

        if not user_details:
            msg = "User Does Not Exist"
            return render(request, "login.html", {"msg": msg})

        hashed_password = user_details[15]  # Password is at index 15
        u_id = user_details[0]  # ID is at index 0
        u_type = user_details[16]  # User type is at index 16
        status = user_details[17]  # Status is at index 17

        if not check_password(password, hashed_password):
            msg = "Incorrect Password"
            return render(request, "login.html", {"msg": msg})

        if status != 1:
            msg = "Your account is not activated"
            return render(request, "login.html", {"msg": msg})

        if u_type == 'admin':
            request.session["admin_id"] = u_id
            return HttpResponseRedirect("/admin_home")
        elif u_type == 'advocate':
            # Check if advocate has selected a category
            s2 = "SELECT category FROM tbl_advocate WHERE u_id = %s"
            c.execute(s2, (u_id,))
            cat_id = c.fetchone()[0]
            
            request.session["adv_id"] = u_id
            
            if not cat_id:
                return HttpResponseRedirect("/adv_home/select_category")
            
            return HttpResponseRedirect("/adv_home")
        elif u_type == 'client':
            request.session["client_id"] = u_id
            return HttpResponseRedirect("/client_home")

        msg = "Invalid user type or credentials"
        return render(request, "login.html", {"msg": msg})

    return render(request, "login.html")
#------------------------------select category----------------------------------
def select_category(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")
    
    adv_id = request.session.get("adv_id")
    
    if request.method == 'POST':
        category_id = request.POST.get("category_id")
        
        # Update the selected category in the database
        s3 = "UPDATE tbl_advocate SET category = %s WHERE u_id = %s"
        c.execute(s3, (category_id, adv_id))
        conn.commit()
        
        return HttpResponseRedirect("/adv_home")
    
    # Fetch available categories from the database
    with conn.cursor() as cursor:
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    # Render the select_category.html template with the list of categories
    return render(request, "advocate/select_category.html", {"categories": categories})
#---------------------------Logout----------------------------------------------#
def logout(request):
    request.session.flush()
    return redirect("login")
#--------------------------forgot password--------------------------------------
#--------------------------password-reset---------------------------------------
def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tbl_user WHERE email = %s", [email])
            user = cursor.fetchone()
            
            if user:
                token = str(uuid.uuid4())
                reset_url = f'http://127.0.0.1:8000/reset/{token}/'
                subject = 'Password Reset'
                message = f'Click the following link to reset your password: {reset_url}'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [email]
                
                email_message = EmailMultiAlternatives(subject, message, from_email, to_email)
                email_message.send()
                
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO password_reset (user_email, token) VALUES (%s, %s)", [email, token])
                    conn.commit()
                msg="Password reset link has been sent to your mail. Kindly check your mail and follow the procedures"
                return render(request, "login.html", {"msg": msg})

            else:
                msg="User with this email does not exist"
                return render(request, "login.html", {"msg": msg})
    return render(request, 'login.html')
#--------------------------------password-confirmation-------------------------------------------------------------------
def password_reset_confirm(request, token):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_email FROM password_reset WHERE token = %s", [token])
                result = cursor.fetchone()
                
                if result:
                    email = result[0]
                    cursor.execute("SELECT u_id FROM tbl_user WHERE email = %s", [email])
                    user_id = cursor.fetchone()
                    
                    if user_id:
                        user_id = user_id[0]
                        hashed_password = make_password(new_password)  # Hashing the new password
                        cursor.execute("UPDATE tbl_user SET password = %s WHERE u_id = %s", [hashed_password, user_id])
                        conn.commit()

                        cursor.execute("DELETE FROM password_reset WHERE token = %s", [token])
                        conn.commit()

                        return redirect('login')
                return render(request, 'password_reset_confirm.html', {'error': 'Invalid or expired token', 'token': token})
        else:
            return render(request, 'password_reset_confirm.html', {'error': 'Passwords do not match', 'token': token})

    return render(request, 'password_reset_confirm.html', {'token': token})
#---------------------------------password-confirmation-end---------------------------------------------

#----------------------------------------Admin-----------------------------------#
def admin_home(request):
    
    if "admin_id" not in request.session:
        return redirect("login")
    response = render(request, 'admin/admin_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
#--------------------------------------Advocate-request-----------------------------
def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    return render(request,'admin/adv_req.html')
@never_cache
def adv_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        s1 = """
        SELECT a.Entrollmentno, u.u_name, u.u_img, u.age, u.email, u.phone, a.adv_qualification1,
               a.adv_qualification2, u.state, u.district, u.pincode, u.id_proof_type, u.id_proof_url, u.u_id
        FROM tbl_advocate a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'advocate'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/adv_req.html", {"msgg": msg})
        
        # Convert the fetched data into a list of dictionaries
        data_list = []
        for row in data:
            data_list.append({
                "Entrollmentno": row[0],
                "u_name": row[1],
                "u_img": row[2].replace('/media/', ''),
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "adv_qualification1": row[6],
                "adv_qualification2": row[7],
                "state": row[8],
                "district": row[9],
                "pincode": row[10],
                "id_proof_type": row[11],
                "id_proof_url": row[12],
                "u_id": row[13]
            })

        print("Data List:", data_list)  # Debug print for data list
        
        return render(request, "admin/adv_req.html", {"data": data_list, "MEDIA_URL": settings.MEDIA_URL})

    except Exception as e:
        print("Exception occurred:", e)  # Print the exception
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})
@never_cache
def action_adv(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='1' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()

            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_adv = "UPDATE tbl_advocate SET status='2' WHERE u_id=%s"
            c.execute(update_query_adv, (reg_id,))
            conn.commit()
            # Fetch the user's phone number
            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            # Send SMS
            message = "Your advocate request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/adv_req/")

    except Exception as e:
        return render(request, "admin/adv_req.html", {"msgg": f"An error occurred: {str(e)}"})
#---------------------client request----------------------------------------------------------->
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    return render(request,'admin/client_req.html')
def client_req(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        s1 = """
        SELECT a.c_id, u.u_name,u.u_img, u.age, u.email, u.phone,  u.state, u.district, u.pincode, u.u_id
        FROM tbl_client a
        JOIN tbl_user u ON a.u_id = u.u_id
        WHERE u.status = '0' AND u.u_type = 'client'
        """
        print("SQL Query:", s1)

        c.execute(s1)
        data = c.fetchall()

        print("Fetched Data:", data)

        if not data:
            msg = "No Requests to show...."
            return render(request, "admin/client_req.html", {"msgg": msg})
        
        data_list = []
        for row in data:
            data_list.append({
                "c_id": row[0],
                "u_name": row[1],
                "u_img": row[2],
                "age": row[3],
                "email": row[4],
                "phone": row[5],
                "state": row[6],
                "district": row[7],
                "pincode": row[8],
                "u_id": row[9]
            })
        
        return render(request, "admin/client_req.html", {"data": data_list})

    except Exception as e:
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})

@never_cache
def action_client(request):
    if "admin_id" not in request.session:
        return redirect("login")
    try:
        reg_id = request.GET.get("reg_id")
        status = request.GET.get("st")
        if status == "Approve":
            update_query = "UPDATE tbl_user SET status='1' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='1' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Approve):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been approved."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

        elif status == "Reject":
            update_query = "UPDATE tbl_user SET status='2' WHERE u_id=%s"
            c.execute(update_query, (reg_id,))
            conn.commit()

            update_query_client = "UPDATE tbl_client SET status='2' WHERE u_id=%s"
            c.execute(update_query_client, (reg_id,))
            conn.commit()

            verify_query = "SELECT status FROM tbl_client WHERE u_id=%s"
            c.execute(verify_query, (reg_id,))
            client_status = c.fetchone()[0]
            print("Updated client status (Reject):", client_status)

            fetch_query = "SELECT phone FROM tbl_user WHERE u_id=%s"
            c.execute(fetch_query, (reg_id,))
            phone_number = c.fetchone()[0]

            message = "Your client request has been rejected."
            sendsms(phone_number, message)

            return redirect("/admin_home/client_req/")

    except Exception as e:
        print("Exception occurred:", e)  
        return render(request, "admin/client_req.html", {"msgg": f"An error occurred: {str(e)}"})
#--------------------------------------- User list ----------------------------------------------------------
#----------------------------------------advocate list-------------------------------------------------------
@never_cache
def approved_advocates_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, a.Entrollmentno, u.u_img, u.age, 
                   a.adv_qualification1, a.adv_qualification2, u.pincode, 
                   u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_type = 'advocate' AND u.status = 1 AND a.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    advocates = []
    for row in rows:
        is_pdf = row[13].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 13
        advocate_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'Entrollmentno': row[6],
            'u_img': row[7],
            'age': row[8],
            'adv_qualification1': row[9],
            'adv_qualification2': row[10],
            'pincode': row[11],
            'id_proof_type': row[12],
            'id_proof_url': row[13],
            'is_pdf': is_pdf
        }
        advocates.append(advocate_data)

    return render(request, 'admin/approved_advocate_list.html', {'advocates': advocates})
#----------------------------------------client list --------------------------------------------------------

def client_list(request):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.email, u.phone, u.state, u.district, u.u_img, u.age, 
                   u.pincode, u.id_proof_type, u.id_proof_url
            FROM tbl_user u
            WHERE u.u_type = 'client' AND u.status = 1
        """)
        rows = cursor.fetchall()

    # Prepare data to include a flag for PDF detection
    clients = []
    for row in rows:
        is_pdf = row[10].lower().endswith('.pdf')  # Assuming 'id_proof_url' is at index 10
        client_data = {
            'u_id': row[0],  # Include u_id
            'u_name': row[1],
            'email': row[2],
            'phone': row[3],
            'state': row[4],
            'district': row[5],
            'u_img': row[6],
            'age': row[7],
            'pincode': row[8],
            'id_proof_type': row[9],
            'id_proof_url': row[10],
            'is_pdf': is_pdf
        }
        clients.append(client_data)

    return render(request, 'admin/client_list.html', {'clients': clients})

#----------------------------------delete advocate------------------------------------------------------------
@never_cache
def delete_advocate(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the advocate to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'advocate'", [u_id])
        cursor.execute("UPDATE tbl_advocate SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the approved advocates list
    return HttpResponseRedirect('/admin_home/approved_advocates/')
#----------------------------------delete client---------------------------------------------------------------
@never_cache
def delete_client(request, u_id):
    with conn.cursor() as cursor:
        # Update the status of the client to 2 (disabled)
        cursor.execute("UPDATE tbl_user SET status = 2 WHERE u_id = %s AND u_type = 'client'", [u_id])
        cursor.execute("UPDATE tbl_client SET status = 2 WHERE u_id = %s", [u_id])
        conn.commit()
    
    # Redirect back to the client list
    return HttpResponseRedirect('/admin_home/client_list/')
#---------------------------------advocate---------------------------------------------------------
def adv_home(request):
    if "adv_id" not in request.session:
        return redirect("login")
    response = render(request, 'advocate/adv_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

#-------------------------------advocate profile view -------------------------------------------------------
@never_cache
def advocate_profile(request):
    if not request.session.get("adv_id"):
        return HttpResponseRedirect("/login")
    
    adv_id = request.session.get("adv_id")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.u_img, u.u_name, u.gender, u.age, u.email, u.phone, 
                u.address, u.state, u.district, u.pincode, 
                u.id_proof_type, u.id_proof_url, 
                a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [adv_id])
        
        advocate_details = cursor.fetchone()
    
    if advocate_details:
        data = {
            "img_url": advocate_details[0],
            "name": advocate_details[1],
            "gender": advocate_details[2],
            "age": advocate_details[3],
            "email": advocate_details[4],
            "phone": advocate_details[5],
            "address": advocate_details[6],
            "state": advocate_details[7],
            "district": advocate_details[8],
            "pincode": advocate_details[9],
            "id_proof_type": advocate_details[10],
            "id_proof_url": advocate_details[11],
            "enrollment_number": advocate_details[12],
            "qualification1": advocate_details[13],
            "qualification2": advocate_details[14],
        }
    else:
        data = {"msg": "Profile not found"}

    return render(request, "advocate/advocate_profile.html", {"data": data})
#---------------------------------------advocate prfile update-----------------------------------------------
@never_cache
def advocate_profile_update(request):
    data = {}

    # Ensure the user is logged in
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    user_id = request.session['adv_id']

    if request.method == 'POST':
        # Get the profile data from the form
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        pincode = request.POST.get("pincode")
        taluk = request.POST.get("taluk")
        village = request.POST.get("village")
        id_proof_type = request.POST.get("idProofType")
        id_proof_file = request.FILES.get("idProofFile")
        img = request.FILES.get("img")
        enrollment_number = request.POST.get("enrollmentNumber")
        qualification1 = request.POST.get("qualifications1")
        qualification2 = request.POST.get("qualifications2")

        with conn.cursor() as cursor:
            # Check if email or phone is being updated to an existing user's email or phone
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_user 
                WHERE (email = %s OR phone = %s) 
                AND u_id != %s
            """, [email, phone, user_id])
            count = cursor.fetchone()[0]

            if count == 0:
                # Update profile image if a new one is uploaded
                if img:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    img_filename = fs.save(img.name, img)
                    img_url = fs.url(img_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET u_img = %s 
                        WHERE u_id = %s
                    """, [img_url, user_id])

                # Update ID proof if a new one is uploaded
                if id_proof_file:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    id_proof_filename = fs.save(id_proof_file.name, id_proof_file)
                    id_proof_url = fs.url(id_proof_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET id_proof_url = %s 
                        WHERE u_id = %s
                    """, [id_proof_url, user_id])

                # Update the rest of the profile information in tbl_user
                cursor.execute("""
                    UPDATE tbl_user 
                    SET u_name = %s, age = %s, gender = %s, email = %s, phone = %s, address = %s, state = %s, district = %s, pincode = %s, taluk = %s, village = %s, id_proof_type = %s
                    WHERE u_id = %s
                """, [name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, user_id])

                # Update advocate-specific information in tbl_advocate
                cursor.execute("""
                    UPDATE tbl_advocate 
                    SET Entrollmentno = %s, adv_qualification1 = %s, adv_qualification2 = %s
                    WHERE u_id = %s
                """, [enrollment_number, qualification1, qualification2, user_id])

                # Commit the transaction
                conn.commit()

                # Update session data if needed
                request.session['adv_name'] = name
                request.session['adv_email'] = email
                request.session['adv_phone'] = phone

                data["msg"] = "Profile updated successfully."
            else:
                data["msg"] = "Email or phone already exists."

    # Fetch current profile data
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.u_img, u.u_name, u.age, u.gender, u.email, u.phone, u.address, u.state, u.district, u.pincode, u.taluk, u.village, u.id_proof_type, u.id_proof_url,
                   a.Entrollmentno, a.adv_qualification1, a.adv_qualification2
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            WHERE u.u_id = %s
        """, [user_id])
        user_details = cursor.fetchone()

    if not user_details:
        data["msg"] = "Profile not found."
    else:
        profile_data = {
            "u_img": user_details[0],
            "name": user_details[1],
            "age": user_details[2],
            "gender": user_details[3],
            "email": user_details[4],
            "phone": user_details[5],
            "address": user_details[6],
            "state": user_details[7],
            "district": user_details[8],
            "pincode": user_details[9],
            "taluk": user_details[10],
            "village": user_details[11],
            "id_proof_type": user_details[12],
            "id_proof_url": user_details[13],
            "enrollment_number": user_details[14],
            "qualification1": user_details[15],
            "qualification2": user_details[16],
        }
        data["profile"] = profile_data

    return render(request, "advocate/advocate_profile_update.html", {"data": data})

#--------------------------------change password-------------------------------------------------------
@never_cache
def change_password_adv(request):
    if 'adv_id' not in request.session:
        print("Client ID not found in session, redirecting to login")
        return HttpResponseRedirect("/login")
    
    client_id = request.session['adv_id']
    print("Advocate ID found in session:", client_id)

    if request.method == 'POST':
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        print("Received POST data:", current_password, new_password, confirm_password)

        if new_password != confirm_password:
            msg = "New passwords do not match"
            print(msg)
            return render(request, "advocate/change_password_adv.html", {"msg": msg})

        with conn.cursor() as c:
            # Assuming client_id is the same as user_id in tbl_login
            s1 = "SELECT password FROM tbl_user WHERE u_id = %s"
            c.execute(s1, (client_id,))
            user_details = c.fetchone()

            if not user_details:
                msg = "User does not exist"
                print(msg)
                return render(request, "advocate/change_password_adv.html", {"msg": msg})

            hashed_password = user_details[0]  

            if not check_password(current_password, hashed_password):
                msg = "Incorrect current password"
                print(msg)
                return render(request, "advocate/change_password_adv.html", {"msg": msg})

            new_hashed_password = make_password(new_password)
            
            s2 = "UPDATE tbl_user SET password = %s WHERE u_id = %s"
            c.execute(s2, (new_hashed_password, client_id))
            conn.commit()  # Commit the transaction

        msg = "Password changed successfully"
        print(msg)
        return render(request, "advocate/change_password_adv.html", {"msg": msg})

    return render(request, "advocate/change_password_adv.html")
#--------------------------------------add case history ------------------------------------------------------
def validate_case_number(case_number):
    if not re.match(r'^CASE-\d{4}-\d{4}$', case_number):
        raise ValidationError('Case number must be in the format CASE-YYYY-NNNN.')
@never_cache
def add_case(request):
    if not request.session.get("adv_id"):
        return redirect('login')

    adv_id = request.session.get("adv_id")  # Get advocate ID from session
    category_choices = []

    # Fetch categories for the dropdown
    with conn.cursor() as cursor:
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = cursor.fetchall()
        category_choices = [(cat_id[0], cat_id[1]) for cat_id in categories]

    if request.method == 'POST':
        case_number = request.POST.get('case_number')
        case_name = request.POST.get('case_name')
        case_status = request.POST.get('case_status')
        case_date = request.POST.get('case_date')
        days_taken = request.POST.get('days_taken')
        court_name = request.POST.get('court_name')
        case_category = request.POST.get('case_category')

        # Validate the case number format
        try:
            validate_case_number(case_number)
        except ValidationError as e:
            return render(request, 'advocate/add_case.html', {
                'error_message': str(e),
                'category_choices': category_choices
            })

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tbl_case_history (advocate_id, case_number, case_name, case_status, case_date, days_taken, court_name, case_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [adv_id, case_number, case_name, case_status, case_date, days_taken, court_name, case_category])
                conn.commit()
        except Exception as e:
            print("Error inserting data:", e)
            conn.rollback()

        return redirect('add_case')  # Redirect to a success page or another page

    return render(request, 'advocate/add_case.html', {'category_choices': category_choices})

#---------------------------------------client----------------------------------------------------------------
def client_home(request):
    if "client_id" not in request.session:
        return redirect("login")
    
    response = render(request, 'client/client_home.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response
##---------------------------------client profile view---------------------------------------------------------
@never_cache
def client_profile_view(request):
    if 'client_id' not in request.session:
        return HttpResponseRedirect('/login')

    client_id = request.session['client_id']

    # Fetch client details
    s1 = "SELECT * FROM tbl_user WHERE u_id = %s"
    c.execute(s1, (client_id,))
    user_details = c.fetchone()

    if not user_details:
        msg = "Client profile not found."
        return render(request, "client/client_profile_view.html", {"msg": msg})

    profile_data = {
        "name": user_details[2],
        "age": user_details[4],
        "gender": user_details[3],
        "email": user_details[5],
        "phone": user_details[6],
        "address": user_details[7],
        "state": user_details[8],
        "district": user_details[9],
        "pincode": user_details[10],
        "taluk": user_details[11],
        "village": user_details[12],
        "id_proof_type": user_details[13],
        "id_proof_url": user_details[14],
        "u_img": user_details[1],  # Assuming user image is at index 0
    }

    # Determine if ID proof is a PDF
    idproof_is_pdf = profile_data['id_proof_url'].endswith('.pdf') if profile_data['id_proof_url'] else False

    return render(request, "client/client_profile_view.html", {
        "profile_data": profile_data,
        "idproof_is_pdf": idproof_is_pdf
    })
#------------------------------client profile update-------------------------------------------------------------
@never_cache
def client_profile_update(request):
    data = {}
    
    # Ensure the user is logged in
    if 'client_id' not in request.session:
        return HttpResponseRedirect('/login')
    
    user_id = request.session['client_id']

    if request.method == 'POST':
        # Get the profile data from the form
        name = request.POST.get("name")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        state = request.POST.get("state")
        district = request.POST.get("district")
        pincode = request.POST.get("pincode")
        taluk = request.POST.get("taluk")
        village = request.POST.get("village")
        id_proof_type = request.POST.get("idProofType")
        id_proof_file = request.FILES.get("idProofFile")
        img = request.FILES.get("img")

        with conn.cursor() as cursor:
            # Check if email or phone is being updated to an existing user's email or phone
            cursor.execute("""
                SELECT COUNT(*) 
                FROM tbl_user 
                WHERE (email = %s OR phone = %s) 
                AND u_id != %s
            """, [email, phone, user_id])
            count = cursor.fetchone()[0]

            if count == 0:
                # Update profile image if a new one is uploaded
                if img:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    img_filename = fs.save(img.name, img)
                    img_url = fs.url(img_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET u_img = %s 
                        WHERE u_id = %s
                    """, [img_url, user_id])

                # Update ID proof if a new one is uploaded
                if id_proof_file:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    id_proof_filename = fs.save(id_proof_file.name, id_proof_file)
                    id_proof_url = fs.url(id_proof_filename)
                    cursor.execute("""
                        UPDATE tbl_user 
                        SET id_proof_url = %s 
                        WHERE u_id = %s
                    """, [id_proof_url, user_id])

                # Update the rest of the profile information
                cursor.execute("""
                    UPDATE tbl_user 
                    SET u_name = %s, age = %s, gender = %s, email = %s, phone = %s, address = %s, state = %s, district = %s, pincode = %s, taluk = %s, village = %s, id_proof_type = %s
                    WHERE u_id = %s
                """, [name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, user_id])

                conn.commit()  

                # Update session data if needed
                request.session['client_name'] = name
                request.session['client_email'] = email
                request.session['client_phone'] = phone

                data["msg"] = "Profile updated successfully."
            else:
                data["msg"] = "Email or phone already exists."

    # Fetch current profile data
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u_img, u_name, age, gender, email, phone, address, state, district, pincode, taluk, village, id_proof_type, id_proof_url 
            FROM tbl_user 
            WHERE u_id = %s
        """, [user_id])
        user_details = cursor.fetchone()

    if not user_details:
        data["msg"] = "Profile not found."
    else:
        profile_data = {
            "u_img": user_details[0],
            "name": user_details[1],
            "age": user_details[2],
            "gender": user_details[3],
            "email": user_details[4],
            "phone": user_details[5],
            "address": user_details[6],
            "state": user_details[7],
            "district": user_details[8],
            "pincode": user_details[9],
            "taluk": user_details[10],
            "village": user_details[11],
            "id_proof_type": user_details[12],
            "id_proof_url": user_details[13],
        }
        data["profile"] = profile_data

    return render(request, "client/client_profile_update.html", {"data": data})
#----------------------------change password------------------------------------------------
def change_password(request):
    if 'client_id' not in request.session:
        print("Client ID not found in session, redirecting to login")
        return HttpResponseRedirect("/login")
    
    client_id = request.session['client_id']
    print("Client ID found in session:", client_id)

    if request.method == 'POST':
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        print("Received POST data:", current_password, new_password, confirm_password)

        if new_password != confirm_password:
            msg = "New passwords do not match"
            print(msg)
            return render(request, "change_password.html", {"msg": msg})

        with conn.cursor() as c:
            # Assuming client_id is the same as user_id in tbl_login
            s1 = "SELECT password FROM tbl_user WHERE u_id = %s"
            c.execute(s1, (client_id,))
            user_details = c.fetchone()

            if not user_details:
                msg = "User does not exist"
                print(msg)
                return render(request, "change_password.html", {"msg": msg})

            hashed_password = user_details[0]  

            if not check_password(current_password, hashed_password):
                msg = "Incorrect current password"
                print(msg)
                return render(request, "change_password.html", {"msg": msg})

            new_hashed_password = make_password(new_password)
            
            s2 = "UPDATE tbl_user SET password = %s WHERE u_id = %s"
            c.execute(s2, (new_hashed_password, client_id))
            conn.commit()  # Commit the transaction

        msg = "Password changed successfully"
        print(msg)
        return render(request, "change_password.html", {"msg": msg})

    return render(request, "change_password.html")
    
#-------------------------------------advocate - search --------------------------------------------------
@never_cache
def get_advocate_profile(request, advocate_id):
    with conn.cursor() as cursor:
        # Fetch advocate details
        cursor.execute("""
            SELECT u.u_id, u.u_name, u.gender, u.age, u.email, u.phone, u.address, u.state, u.district,
                   u.pincode, u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_img,
                   a.Entrollmentno, a.adv_qualification1, a.adv_qualification2, a.adv_qualification3,
                   c.category_name
            FROM tbl_user u
            JOIN tbl_advocate a ON u.u_id = a.u_id
            LEFT JOIN tbl_category c ON a.category = c.cat_id
            WHERE u.u_id = %s AND u.u_type = 'advocate'
        """, [advocate_id])
        advocate_details = cursor.fetchone()

        if not advocate_details:
            return JsonResponse({'error': 'Advocate not found'}, status=404)

        # Fetch case history
        cursor.execute("""
            SELECT case_number, case_name, case_status, case_date, days_taken, court_name, case_category
            FROM tbl_case_history
            WHERE advocate_id = %s
        """, [advocate_id])
        case_history = cursor.fetchall()

    profile_data = {
        'u_id': advocate_details[0],
        'name': advocate_details[1],
        'gender': advocate_details[2],
        'age': advocate_details[3],
        'email': advocate_details[4],
        'phone': advocate_details[5],
        'address': advocate_details[6],
        'state': advocate_details[7],
        'district': advocate_details[8],
        'pincode': advocate_details[9],
        'taluk': advocate_details[10],
        'village': advocate_details[11],
        'id_proof_type': advocate_details[12],
        'id_proof_url': advocate_details[13],
        'u_img': advocate_details[14],
        'enrollment_number': advocate_details[15],
        'qualification1': advocate_details[16],
        'qualification2': advocate_details[17],
        'qualification3': advocate_details[18],
        'category': advocate_details[19],
        'case_history': [
            {
                'case_number': case[0],
                'case_name': case[1],
                'case_status': case[2],
                'case_date': case[3].strftime('%Y-%m-%d') if case[3] else None,
                'days_taken': case[4],
                'court_name': case[5],
                'case_category': case[6]
            } for case in case_history
        ]
    }
    return JsonResponse(profile_data)
@csrf_exempt
@never_cache
def advocate_list(request):
    if "client_id" not in request.session:
        return redirect("login")
    
    client_id = request.session.get('client_id')

    # Initialize request_statuses as an empty dictionary
    request_statuses = {}

    # Get filter parameters
    district = request.GET.get('district')
    category = request.GET.get('category')
    rating = request.GET.get('rating')
    sort_by = request.GET.get('sort_by', 'rating')  # Default sort by rating
    
    # Base query
    query = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img, c.category_name,
           AVG(r.rating) AS average_rating, COUNT(r.rating_id) AS review_count
    FROM tbl_user u
    LEFT JOIN tbl_advocate a ON u.u_id = a.u_id
    LEFT JOIN tbl_category c ON a.category = c.cat_id
    LEFT JOIN tbl_rating r ON a.u_id = r.advocate_id
    WHERE u.u_type = 'advocate' AND u.status = 1
    """
    
    params = []
    
    # Add filters
    if district:
        query += " AND u.district = %s"
        params.append(district)
    if category:
        query += " AND c.cat_id = %s"
        params.append(category)
    
    query += " GROUP BY u.u_id"
    
    # Add rating filter after grouping
    if rating:
        query += " HAVING average_rating >= %s"
        params.append(float(rating))
    
    # Add sorting
    if sort_by == 'rating':
        query += " ORDER BY average_rating DESC"
    elif sort_by == 'name':
        query += " ORDER BY u.u_name ASC"
    
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        advocates = cursor.fetchall()
    
    # Process advocates data
    advocates_list = []
    for advocate in advocates:
        advocate_dict = {
            'u_id': advocate[0],
            'u_name': advocate[1],
            'gender': advocate[2],
            'age': advocate[3],
            'address': advocate[4],
            'state': advocate[5],
            'district': advocate[6],
            'taluk': advocate[7],
            'village': advocate[8],
            'id_proof_type': advocate[9],
            'id_proof_url': advocate[10],
            'u_type': advocate[11],
            'email': advocate[12][:3] + '****' + '@' + advocate[12].split('@')[1],
            'phone': advocate[13][:3] + '****' + advocate[13][-2:],
            'u_img': advocate[14],
            'category_name': advocate[15],
            'average_rating': round(advocate[16], 1) if advocate[16] else 0,
            'review_count': advocate[17]
        }
        advocates_list.append(advocate_dict)
    
    # Paginate the advocates list
    paginator = Paginator(advocates_list, 10)  # Show 10 advocates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all districts and categories for filtering
    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT district FROM tbl_user WHERE u_type = 'advocate'")
        districts = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
    context = {
        'page_obj': page_obj,
        'districts': districts,
        'categories': categories,
        'star_range': range(1, 6),
        'current_filters': {
            'district': district,
            'category': category,
            'rating': rating,
            'sort_by': sort_by
        }
    }

    # Use request_statuses in the context
    return render(request, 'client/advocate_list.html', {
        'request_statuses': request_statuses,
        'page_obj': page_obj,
        'districts': districts,
        'categories': categories,
        'star_range': range(1, 6),
        'current_filters': {
            'district': district,
            'category': category,
            'rating': rating,
            'sort_by': sort_by
        }
    })

from datetime import datetime
@never_cache
def view_advocate_profile(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")
    
    client_id = request.session.get('client_id')
    
    # Fetch advocate profile
    query_advocate = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img, c.category_name,
           AVG(r.rating) AS average_rating, COUNT(r.rating_id) AS review_count
    FROM tbl_user u
    LEFT JOIN tbl_advocate a ON u.u_id = a.u_id
    LEFT JOIN tbl_category c ON a.category = c.cat_id
    LEFT JOIN tbl_rating r ON a.u_id = r.advocate_id
    WHERE u.u_id = %s AND u.u_type = 'advocate' AND u.status = 1
    GROUP BY u.u_id
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query_advocate, [advocate_id])
        advocate = cursor.fetchone()
    
    if not advocate:
        return HttpResponse("Advocate not found", status=404)
    
    advocate_dict = {
        'u_id': advocate[0],
        'u_name': advocate[1],
        'gender': advocate[2],
        'age': advocate[3],
        'address': advocate[4],
        'state': advocate[5],
        'district': advocate[6],
        'taluk': advocate[7],
        'village': advocate[8],
        'id_proof_type': advocate[9],
        'id_proof_url': advocate[10],
        'u_type': advocate[11],
        'email': advocate[12],
        'phone': advocate[13],
        'u_img': advocate[14],
        'category_name': advocate[15],
        'average_rating': round(advocate[16], 1) if advocate[16] else 0,
        'review_count': advocate[17]
    }
    
    # Fetch advocate's case history with category name
    query_cases = """
    SELECT ch.case_history_id, ch.case_number, ch.case_name, ch.case_status, 
           ch.case_date, ch.days_taken, ch.court_name, cat.category_name
    FROM tbl_case_history ch
    JOIN tbl_category cat ON ch.case_category = cat.cat_id
    WHERE ch.advocate_id = %s
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query_cases, [advocate_id])
        case_history = cursor.fetchall()
    
    paginator = Paginator(case_history, 10)  # Show 10 cases per page
    page_number = request.GET.get('page')
    cases_page_obj = paginator.get_page(page_number)
    
    case_history_list = [{
        'case_id': case[0],
        'case_number': case[1],
        'case_name': case[2],
        'case_status': case[3],
        'case_date': datetime.strptime(case[4], '%Y-%m-%d').strftime('%Y-%m-%d') if isinstance(case[4], str) else case[4].strftime('%Y-%m-%d'),
        'days_taken': case[5],
        'court_name': case[6],
        'case_category': case[7]
    } for case in cases_page_obj]
    
    context = {
    'advocate': advocate_dict,
    'case_history': case_history_list,
    'page_obj': cases_page_obj,
    'client_id': client_id,
    'adv_id': advocate_dict['u_id'],  # Ensure this is set correctly
    }
    return render(request, 'client/advocate_profile.html', context)

    #{% url 'register_case' %}?advocate_id={{ advocate.u_id }} {% url 'chat_with_advocate' advocate.u_id %}
import os
from datetime import datetime
import pymysql
from django.shortcuts import render, redirect
from django.conf import settings
from home.classify_document import classify_document  # Adjust the import based on where classify_document is defined

# Establish MySQL connection
conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")

import os
from datetime import datetime
import pymysql
from django.shortcuts import render, redirect
from django.conf import settings
from home.classify_document import classify_document  # Adjust the import based on where classify_document is defined
from PIL import Image
from docx2pdf import convert as docx_to_pdf
import os
import mimetypes
from datetime import datetime
from django.conf import settings
# Establish MySQL connection

conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")

from django.shortcuts import render, redirect
from django.conf import settings
from .classification import classify_document
from PyPDF2 import PdfReader 
import os
@never_cache
def register_case(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")

    client_id = request.session.get('client_id')

    if request.method == "POST":
        case_name = request.POST.get("case_name")
        supporting_documents = request.FILES.getlist("supporting_documents")
        
        for doc in supporting_documents:
            if doc.name.endswith('.pdf'):
                # Save the PDF file temporarily
                pdf_path = os.path.join(settings.MEDIA_ROOT, 'case_documents', doc.name)
                with open(pdf_path, 'wb+') as destination:
                    for chunk in doc.chunks():
                        destination.write(chunk)
                
                # Extract text from the PDF
                with open(pdf_path, 'rb') as file:
                    reader = PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                
                # Classify the document
                classification = classify_document(text)
                
                # Insert the new case into the database (add classification)
                query = """
                INSERT INTO tbl_case (client_id, advocate_id, case_name, classification, status)
                VALUES (%s, %s, %s, %s, %s)
                """
                with conn.cursor() as cursor:
                    cursor.execute(query, [client_id, advocate_id, case_name, classification, "Pending"])
                
                # Optionally, remove the temporary PDF file
                os.remove(pdf_path)

        return redirect("advocate_profile_view", advocate_id=advocate_id)

    return render(request, "client/register_case.html", {'advocate_id': advocate_id})

# Helper functions for conversion
def convert_image_to_pdf(image_file, doc_name):
    img = Image.open(image_file)
    pdf_name = doc_name.replace(image_file.name.split('.')[-1], "pdf")
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'case_documents', pdf_name)

    img.convert('RGB').save(pdf_path)
    return f"case_documents/{pdf_name}"

def convert_word_to_pdf(word_file, doc_name):
    word_path = os.path.join(settings.MEDIA_ROOT, 'case_documents', word_file.name)
    with open(word_path, 'wb+') as destination:
        for chunk in word_file.chunks():
            destination.write(chunk)
    
    # Convert DOCX to PDF
    pdf_name = doc_name.replace(".docx", ".pdf")
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'case_documents', pdf_name)
    docx_to_pdf(word_path, pdf_path)
    
    # Optionally, remove the original DOCX after conversion
    os.remove(word_path)

    return f"case_documents/{pdf_name}"
@never_cache
def client_request(request):
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    advocate_id = request.session['adv_id']  # Corrected variable name

    # Fetch pending cases with client_id
    query = """
    SELECT c.case_id, c.case_name, c.case_description, c.case_date, u.u_name, u.email, u.u_id
    FROM tbl_case c
    JOIN tbl_user u ON c.client_id = u.u_id
    WHERE c.advocate_id = %s AND c.status = 'Pending'
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [advocate_id])
        pending_cases = cursor.fetchall()
    
    cases_list = [{
        'case_id': case[0],
        'case_name': case[1],
        'case_description': case[2],
        'case_date': case[3],
        'client_name': case[4],
        'client_email': case[5],
        'client_id': case[6]  # Include client_id
    } for case in pending_cases]
    
    context = {
        'pending_cases': cases_list
    }
    
    return render(request, 'advocate/client_request.html', context)

def handle_case(request, case_id, action):
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    advocate_id = request.session['adv_id']
    # Update case status
    status = 'Accepted' if action == 'accept' else 'Rejected'
    query = "UPDATE tbl_case SET status = %s WHERE case_id = %s AND advocate_id = %s"
    
    with conn.cursor() as cursor:
        cursor.execute(query, [status, case_id, advocate_id])
    conn.commit()
    
    # Fetch client email
    query_client = "SELECT email FROM tbl_case JOIN tbl_user ON tbl_case.client_id = tbl_user.u_id WHERE tbl_case.case_id = %s"
    
    with conn.cursor() as cursor:
        cursor.execute(query_client, [case_id])
        client_email = cursor.fetchone()[0]
    
    # Send notification to the client
    send_mail(
        'Case Status Update',
         f'Dear Client,\n\nWe regret to inform you that your case request has been {status.lower()} by the advocate. We understand that this may be disappointing news and sincerely apologize for any inconvenience this may cause.\n\nThank you for your understanding and patience throughout this process.\n\nBest regards,\nThe Legal Advisor Team',
        settings.DEFAULT_FROM_EMAIL,
        [client_email],
        fail_silently=False,
    )
    
    return redirect("client_request")

from django.conf import settings
@never_cache
def view_client_details(request, client_id):
    if "adv_id" not in request.session:
        return redirect("login")
    advocate_id = request.session['adv_id']

    # Fetch client profile details
    query_client = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img
    FROM tbl_user u
    WHERE u.u_id = %s AND u.u_type = 'client'
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_client, [client_id])
        client = cursor.fetchone()
    
    if not client:
        return HttpResponse("Client not found", status=404)
    
    client_dict = {
        'u_id': client[0],
        'u_name': client[1],
        'gender': client[2],
        'age': client[3],
        'address': client[4],
        'state': client[5],
        'district': client[6],
        'taluk': client[7],
        'village': client[8],
        'id_proof_type': client[9],
        'id_proof_url': client[10],
        'u_type': client[11],
        'email': client[12],
        'phone': client[13],
        'u_img': client[14],
    }
    
    # Fetch accepted case history for the client
    query_case_history = """
    SELECT c.case_id, c.case_name, c.case_description, c.legal_issue, c.incident_date, c.service_type, 
           c.expected_outcome, c.priority_level, c.deadline, c.case_date, c.supporting_documents, c.status
    FROM tbl_case c
    WHERE c.client_id = %s AND c.status = 'Accepted'
    ORDER BY c.case_date DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_case_history, [client_id])
        case_history = cursor.fetchall()
    
    case_history_list = []
    for case in case_history:
        case_history_list.append({
            'case_id': case[0],
            'case_name': case[1],
            'case_description': case[2],
            'legal_issue': case[3],
            'incident_date': case[4],
            'service_type': case[5],
            'expected_outcome': case[6],
            'priority_level': case[7],
            'deadline': case[8],
            'case_date': case[9],
            'supporting_documents': case[10],
            'status': case[11],
        })
    
    context = {
        'client': client_dict,
        'case_history': case_history_list,
        'adv_id': advocate_id,
    }
    
    
    return render(request, 'advocate/client_details.html', context)

@never_cache
def view_case_details(request, case_id):
    if "adv_id" not in request.session:
        return redirect("login")

    # Fetch case details
    query_case = """
    SELECT c.case_id, c.case_name, c.case_description, c.legal_issue, c.incident_date,
           c.service_type, c.expected_outcome, c.priority_level, c.deadline,
           c.case_date, c.supporting_documents, c.status, u.u_name AS client_name,
           u.email AS client_email
    FROM tbl_case c
    JOIN tbl_user u ON c.client_id = u.u_id
    WHERE c.case_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_case, [case_id])
        case_details = cursor.fetchone()
    
    if not case_details:
        return HttpResponse("Case not found", status=404)

    # Split the supporting_documents field and convert paths to URLs
    supporting_documents = case_details[10].split(',') if case_details[10] else []
    supporting_documents = [doc.replace('media/', '', 1) for doc in supporting_documents]
    supporting_documents = [f"{settings.MEDIA_URL}{doc}" for doc in supporting_documents]
    case_dict = {
        'case_id': case_details[0],
        'case_name': case_details[1],
        'case_description': case_details[2],
        'legal_issue': case_details[3],
        'incident_date': case_details[4],
        'service_type': case_details[5],
        'expected_outcome': case_details[6],
        'priority_level': case_details[7],
        'deadline': case_details[8],
        'case_date': case_details[9],
        'supporting_documents': supporting_documents,
        'status': case_details[11],
        'client_name': case_details[12],
        'client_email': case_details[13],
    }

    context = {
        'case': case_dict,
    }
    
    return render(request, 'advocate/case_details.html', context)


def client_previous_req(request):
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    advocate_id = request.session['adv_id']

    # Fetch all cases (Pending, Accepted, Rejected) with client information
    query = """
    SELECT c.case_id, c.case_name, c.case_description, c.case_date, u.u_name, u.email, u.u_id, c.status
    FROM tbl_case c
    JOIN tbl_user u ON c.client_id = u.u_id
    WHERE c.advocate_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [advocate_id])
        cases = cursor.fetchall()
    
    cases_list = [{
        'case_id': case[0],
        'case_name': case[1],
        'case_description': case[2],
        'case_date': case[3],
        'client_name': case[4],
        'client_email': case[5],
        'client_id': case[6], 
        'status': case[7]
    } for case in cases]

    # Set up pagination
    paginator = Paginator(cases_list, 10)  # Show 10 cases per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'advocate/client_previous_req.html', context)
@never_cache
def client_list(request):
    if 'adv_id' not in request.session:
        return HttpResponseRedirect('/login')

    advocate_id = request.session['adv_id']

    # Fetch distinct clients for whom the advocate has accepted cases
    query = """
    SELECT DISTINCT u.u_id, u.u_name, u.email, u.phone, u.u_img, MIN(c.case_date) as case_accepted_date
    FROM tbl_case c
    JOIN tbl_user u ON c.client_id = u.u_id
    WHERE c.advocate_id = %s AND c.status = 'Accepted'
    GROUP BY u.u_id, u.u_name, u.email, u.phone, u.u_img
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [advocate_id])
        accepted_clients = cursor.fetchall()

    clients_list = [{
        'u_id': client[0],
        'u_name': client[1],
        'email': client[2],
        'phone': client[3],
        'u_img': client[4],
        'case_accepted_date': client[5],
    } for client in accepted_clients]

    # Pagination setup
    paginator = Paginator(clients_list, 9)  # Show 9 clients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'advocate/client_list.html', context)
@never_cache
def advocate_list_for_client(request):
    if "client_id" not in request.session:
        return redirect("login")

    client_id = request.session.get('client_id')

    # Initialize request_statuses as an empty dictionary
    request_statuses = {}

    # Get filter parameters
    district = request.GET.get('district')
    category = request.GET.get('category')
    rating = request.GET.get('rating')
    sort_by = request.GET.get('sort_by', 'rating')  # Default sort by rating

    # Base query to only fetch advocates who have accepted the client's case requests
    query = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img, c.category_name,
           AVG(r.rating) AS average_rating, COUNT(r.rating_id) AS review_count
    FROM tbl_user u
    LEFT JOIN tbl_advocate a ON u.u_id = a.u_id
    LEFT JOIN tbl_category c ON a.category = c.cat_id
    LEFT JOIN tbl_rating r ON a.u_id = r.advocate_id
    JOIN tbl_case t ON t.advocate_id = u.u_id
    WHERE u.u_type = 'advocate' AND u.status = 1 
    AND t.client_id = %s AND t.status = 'Accepted'
    """
    
    params = [client_id]
    
    # Add filters
    if district:
        query += " AND u.district = %s"
        params.append(district)
    if category:
        query += " AND c.cat_id = %s"
        params.append(category)
    
    query += " GROUP BY u.u_id"
    
    # Add rating filter after grouping
    if rating:
        query += " HAVING average_rating >= %s"
        params.append(float(rating))
    
    # Add sorting
    if sort_by == 'rating':
        query += " ORDER BY average_rating DESC"
    elif sort_by == 'name':
        query += " ORDER BY u.u_name ASC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        advocates = cursor.fetchall()

    # Process advocates data
    advocates_list = []
    for advocate in advocates:
        advocate_dict = {
            'u_id': advocate[0],
            'u_name': advocate[1],
            'gender': advocate[2],
            'age': advocate[3],
            'address': advocate[4],
            'state': advocate[5],
            'district': advocate[6],
            'taluk': advocate[7],
            'village': advocate[8],
            'id_proof_type': advocate[9],
            'id_proof_url': advocate[10],
            'u_type': advocate[11],
            'email': advocate[12][:3] + '****' + '@' + advocate[12].split('@')[1],
            'phone': advocate[13][:3] + '****' + advocate[13][-2:],
            'u_img': advocate[14],
            'category_name': advocate[15],
            'average_rating': round(advocate[16], 1) if advocate[16] else 0,
            'review_count': advocate[17]
        }
        advocates_list.append(advocate_dict)

    # Paginate the advocates list
    paginator = Paginator(advocates_list, 10)  # Show 10 advocates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all districts and categories for filtering
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT district FROM tbl_user WHERE u_type = 'advocate'")
        districts = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT cat_id, category_name FROM tbl_category")
        categories = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    context = {
        'page_obj': page_obj,
        'districts': districts,
        'categories': categories,
        'star_range': range(1, 6),
        'current_filters': {
            'district': district,
            'category': category,
            'rating': rating,
            'sort_by': sort_by
        },
        'request_statuses': request_statuses
    }

    return render(request, 'client/advocate_list.html', context)
@never_cache
def accepted_advocate_profile(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")
    
    client_id = request.session.get('client_id')
    
    # Fetch advocate profile
    query_advocate = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img, c.category_name,
           AVG(r.rating) AS average_rating, COUNT(r.rating_id) AS review_count
    FROM tbl_user u
    LEFT JOIN tbl_advocate a ON u.u_id = a.u_id
    LEFT JOIN tbl_category c ON a.category = c.cat_id
    LEFT JOIN tbl_rating r ON a.u_id = r.advocate_id
    WHERE u.u_id = %s AND u.u_type = 'advocate' AND u.status = 1
    GROUP BY u.u_id
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query_advocate, [advocate_id])
        advocate = cursor.fetchone()
    
    if not advocate:
        return HttpResponse("Advocate not found", status=404)
    
    advocate_dict = {
        'u_id': advocate[0],
        'u_name': advocate[1],
        'gender': advocate[2],
        'age': advocate[3],
        'address': advocate[4],
        'state': advocate[5],
        'district': advocate[6],
        'taluk': advocate[7],
        'village': advocate[8],
        'id_proof_type': advocate[9],
        'id_proof_url': advocate[10],
        'u_type': advocate[11],
        'email': advocate[12],
        'phone': advocate[13],
        'u_img': advocate[14],
        'category_name': advocate[15],
        'average_rating': round(advocate[16], 1) if advocate[16] else 0,
        'review_count': advocate[17]
    }
    
    # Fetch advocate's case history with category name
    query_cases = """
    SELECT ch.case_history_id, ch.case_number, ch.case_name, ch.case_status, 
           ch.case_date, ch.days_taken, ch.court_name, cat.category_name
    FROM tbl_case_history ch
    JOIN tbl_category cat ON ch.case_category = cat.cat_id
    WHERE ch.advocate_id = %s
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query_cases, [advocate_id])
        case_history = cursor.fetchall()
    
    paginator = Paginator(case_history, 10)  # Show 10 cases per page
    page_number = request.GET.get('page')
    cases_page_obj = paginator.get_page(page_number)
    
    case_history_list = [{
        'case_id': case[0],
        'case_number': case[1],
        'case_name': case[2],
        'case_status': case[3],
        'case_date': datetime.strptime(case[4], '%Y-%m-%d').strftime('%Y-%m-%d') if isinstance(case[4], str) else case[4].strftime('%Y-%m-%d'),
        'days_taken': case[5],
        'court_name': case[6],
        'case_category': case[7]
    } for case in cases_page_obj]
    
    context = {
        'advocate': advocate_dict,
        'case_history': case_history_list,
        'page_obj': cases_page_obj,
        'client_id': client_id,
    }
    return render(request, 'client/accepted_advocate_profile.html', context)

#-----------------------------chat-----------------------------------------------------

def get_chat_history(client_id, advocate_id):
    conn = pymysql.connect(host='localhost', user='root', password='', db='legal_advisor')
    cursor = conn.cursor()
    query = """
    SELECT * FROM tbl_chat 
    WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
    ORDER BY timestamp ASC
    """
    cursor.execute(query, (client_id, advocate_id, advocate_id, client_id))
    messages = cursor.fetchall()
    conn.close()
    return messages

# home/views.py
from django.shortcuts import render

# views.py
def chat_view(request, client_id, advocate_id):
    # Add logic for handling chat based on client_id and advocate_id
    return render(request, 'chat.html', {'client_id': client_id, 'advocate_id': advocate_id})

#------------------------------------Document - classification --------------------------------------
# views.py

from django.shortcuts import render
import PyPDF2
import pytesseract
from PIL import Image
from .classification import classify_document  # Updated import

# Ensure Tesseract path is set correctly
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_document(document):
    if document.name.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(document)
        text = ''
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    elif document.name.endswith(('.png', '.jpg', '.jpeg')):
        image = Image.open(document)
        text = pytesseract.image_to_string(image)
        return text
    return ''
def document_classification(request):
    classification = None
    if request.method == 'POST':
        document = request.FILES['document']
        text = extract_text_from_document(document)
        print(f"Extracted text: {text}")  # Add this to verify the extracted text

        # Test classification on a known string
        test_text = "This is a case about theft involving stolen goods."
        classification = classify_document(test_text)
        print(f"Manual Test Classification: {classification}")
        
        if text:
            classification = classify_document(text)
        else:
            classification = 'No text found in the document.'

    return render(request, 'advocate/document_classification.html', {'classification': classification})

#-----------------------------------------------payment---------------------------------------------

import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
import pymysql
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def payment_view(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")

    client_id = request.session.get('client_id')
    print(f"Client ID: {client_id}")  # Debug print

    if client_id is None:
        return HttpResponse("Client ID not found.")

    consultation_fee = 500  # Fixed consultation fee
    admin_commission = 200
    total_amount = consultation_fee + admin_commission

    # Create Razorpay Order
    amount_in_paise = total_amount * 100  # Convert to paise
    payment_order = razorpay_client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1'
    })
    
    order_id = payment_order['id']

    # Store order details directly into MySQL using pymysql
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
        cursor = conn.cursor()
    
        insert_payment_query = """INSERT INTO tbl_payment (client_id, advocate_id, amount_paid, payment_date, 
                              payment_status, admin_commission, consultation_fee, total_amount, order_id)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
        values = (client_id, advocate_id, 0, datetime.now(), 'pending', admin_commission, consultation_fee, total_amount,order_id)
        print(f"Inserting payment details: {values}")  # Debug print
    
        cursor.execute(insert_payment_query, values)
        conn.commit()
        print("Payment details inserted successfully.")
    except pymysql.MySQLError as e:
        print(f"Error inserting payment details: {e}")  # Log any SQL error
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    context = {
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order_id,
        'amount': total_amount,
        'currency': 'INR',
        'advocate_id': advocate_id,
        'client_id': client_id,
    }

    return render(request, 'client/payment.html', context)

@csrf_protect

def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        try:
            # Verifying the signature
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            # Update payment details in the database
            conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
            cursor = conn.cursor()

            update_payment_query = """UPDATE tbl_payment SET payment_status = %s, payment_date = %s,
                                      amount_paid = %s WHERE order_id = %s"""
            
            cursor.execute(update_payment_query, ('completed', datetime.now(), request.POST.get('amount'), order_id))
            conn.commit()
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'Payment verification failed'})
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            return JsonResponse({'status': 'Database update failed'})
        finally:
            conn.close()

        return JsonResponse({'status': 'Payment successful'})

    return redirect('client/advocate_profile.html')

def admin_payment_history(request):
    conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    query = """
        SELECT 
            p.client_id, p.advocate_id, p.total_amount, p.payment_status, 
            p.payment_date, p.admin_commission, p.consultation_fee, 
            c.u_name AS client_name, a.u_name AS advocate_name
        FROM 
            tbl_payment p
        LEFT JOIN 
            tbl_user c ON p.client_id = c.u_id
        LEFT JOIN 
            tbl_user a ON p.advocate_id = a.u_id
        WHERE 
            p.payment_status = 'completed'
    """
    
    cursor.execute(query)
    payment_history = cursor.fetchall()
    conn.close()
    
    return render(request, 'admin/payment_history.html', {'payment_history': payment_history})

def advocate_payment_history(request):
    advocate_id = request.session.get('adv_id')
    conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    query = """
        SELECT 
            p.client_id, p.total_amount, p.payment_status, p.payment_date, c.u_name as client_name
        FROM 
            tbl_payment p
        LEFT JOIN 
            tbl_user c ON p.client_id = c.u_id
        WHERE 
            p.advocate_id = %s  and p.payment_status = 'completed'
    """
    
    cursor.execute(query, (advocate_id,))
    payment_history = cursor.fetchall()
    conn.close()
    
    return render(request, 'advocate/payment_history.html', {'payment_history': payment_history})
def client_payment_history(request):
    client_id = request.session.get('client_id')  # Assuming client_id is stored in session after login
    conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    query = """
        SELECT 
            p.total_amount, p.payment_status, p.payment_date, a.u_name as advocate_name
        FROM 
            tbl_payment p
        LEFT JOIN 
            tbl_user a ON p.advocate_id = a.u_id
        WHERE 
            p.client_id = %s
            AND p.payment_status = 'Completed'
    """
    
    cursor.execute(query, (client_id,))
    payment_history = cursor.fetchall()
    conn.close()

    return render(request, 'client/payment_history.html', {'payment_history': payment_history})

def previous_case_requests(request):
    advocate_id = request.session.get('advocate_id')  # Assuming advocate_id is stored in the session
    sort_option = request.GET.get('sort', '')  # Get the sorting option from the query parameters

    conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Base query
    query = """
        SELECT c.case_name, c.case_description, c.case_date, u.u_name as client_name, u.u_email as client_email, c.status, c.client_id
        FROM tbl_case_requests c
        LEFT JOIN tbl_user u ON c.client_id = u.u_id
        WHERE c.advocate_id = %s
    """
    
    # Modify query based on the sorting option
    if sort_option == 'accepted':
        query += " AND c.status = 'Accepted'"
    elif sort_option == 'rejected':
        query += " AND c.status = 'Rejected'"
    
    cursor.execute(query, (advocate_id,))
    cases = cursor.fetchall()
    conn.close()
    
    # Implement pagination if needed
    paginator = Paginator(cases, 10)  # Show 10 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'advocate/previous_case_requests.html', {'page_obj': page_obj})
#------------------------------ IPC-section admin-add---------------------------------------------------------
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.db import connection, transaction
from django.core.files.storage import FileSystemStorage
import csv

def ipc_section(request):
    msgg = ""
    if request.method == "POST":
        # Handle CSV upload
        if 'ipc_csv' in request.FILES:
            csv_file = request.FILES['ipc_csv']
            if not csv_file.name.endswith('.csv'):
                msgg = "Please upload a valid CSV file."
            else:
                fs = FileSystemStorage()
                filename = fs.save(csv_file.name, csv_file)
                filepath = fs.path(filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        for row in reader:
                            if len(row) == 2:
                                ipc_section, ipc_description = row
                                # Check for duplicates
                                with connection.cursor() as cursor:
                                    cursor.execute("SELECT COUNT(*) FROM tbl_ipc WHERE ipc_section = %s", [ipc_section])
                                    if cursor.fetchone()[0] == 0:
                                        cursor.execute("INSERT INTO tbl_ipc (ipc_section, ipc_description) VALUES (%s, %s)", [ipc_section, ipc_description])
                    msgg = "IPC Sections added successfully from CSV"
                except Exception as e:
                    msgg = f"Error inserting data from CSV: {e}"

        # Handle single form submission
        elif request.POST.get('ipc_section'):
            ipc_section = request.POST.get('ipc_section')
            ipc_description = request.POST.get('ipc_description')

            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        # Check for duplicates
                        cursor.execute("SELECT COUNT(*) FROM tbl_ipc WHERE ipc_section = %s", [ipc_section])
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("INSERT INTO tbl_ipc (ipc_section, ipc_description) VALUES (%s, %s)", [ipc_section, ipc_description])
                            msgg = "IPC Section added successfully"
                        else:
                            msgg = "IPC Section already exists"
            except Exception as e:
                msgg = f"Error inserting data: {e}"

    # Fetch existing IPC sections
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, ipc_section, ipc_description FROM tbl_ipc")
            data1 = cursor.fetchall()
    except Exception as e:
        msgg = f"Error fetching data: {e}"
        data1 = []

    # Pagination logic
    paginator = Paginator(data1, 6)  # Show 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/ipc_section.html', {
        'page_obj': page_obj,
        'msgg': msgg
    })

def ipc_remove(request):
    ipc_id = request.GET.get('ipc_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tbl_ipc WHERE id = %s", [ipc_id])
    except Exception as e:
        return redirect('ipc_section', msg=f"Error deleting entry: {e}")
    return redirect('ipc_section')

def ipc_bulk_delete(request):
    if request.method == 'POST':
        ipc_ids = request.POST.getlist('ipc_ids')
        if ipc_ids:
            try:
                with connection.cursor() as cursor:
                    # Using parameterized queries to avoid SQL injection
                    ids_placeholder = ','.join(['%s'] * len(ipc_ids))
                    cursor.execute(f"DELETE FROM tbl_ipc WHERE id IN ({ids_placeholder})", ipc_ids)
            except Exception as e:
                return redirect('ipc_section', msg=f"Error deleting entries: {e}")
    return redirect('ipc_section')
#----------------------ipc-search - client----------------------------------------------------------------

def ipc_search(request):
    ipc_section = request.GET.get('ipc_section', '').strip()
    results = []

    if ipc_section:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ipc_section, ipc_description 
                FROM tbl_ipc 
                WHERE ipc_section = %s OR LOWER(ipc_description) LIKE LOWER(%s)
            """, [ipc_section, f"%{ipc_section}%"])
            results = cursor.fetchall()

    return render(request, 'client/ipc_search.html', {'ipc_results': results, 'ipc_section': ipc_section})

#----------------------------------------client-request-view-------------------------------------------------
@never_cache
def view_client_basic_details(request, client_id):
    if "adv_id" not in request.session:
        return redirect("login")
    advocate_id = request.session['adv_id']

    # Fetch client profile details
    query_client = """
    SELECT u.u_id, u.u_name, u.gender, u.age, u.address, u.state, u.district, 
           u.taluk, u.village, u.id_proof_type, u.id_proof_url, u.u_type, 
           u.email, u.phone, u.u_img
    FROM tbl_user u
    WHERE u.u_id = %s AND u.u_type = 'client'
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_client, [client_id])
        client = cursor.fetchone()
    
    if not client:
        return HttpResponse("Client not found", status=404)
    
    client_dict = {
        'u_id': client[0],
        'u_name': client[1],
        'gender': client[2],
        'age': client[3],
        'address': client[4],
        'state': client[5],
        'district': client[6],
        'taluk': client[7],
        'village': client[8],
        'id_proof_type': client[9],
        'id_proof_url': client[10],
        'u_type': client[11],
        'email': client[12],
        'phone': client[13],
        'u_img': client[14],
    }
    
    # Fetch accepted case history for the client, including advocate names
    query_case_history = """
    SELECT c.case_id, c.case_name, c.case_description, c.legal_issue, c.incident_date, c.service_type, 
           c.expected_outcome, c.priority_level, c.deadline, c.case_date, c.supporting_documents, c.status,
           a.u_name AS advocate_name
    FROM tbl_case c
    JOIN tbl_user a ON c.advocate_id = a.u_id
    WHERE c.client_id = %s AND c.status = 'Accepted'
    ORDER BY c.case_date DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query_case_history, [client_id])
        case_history = cursor.fetchall()
    
    case_history_list = []
    for case in case_history:
        case_history_list.append({
            'case_id': case[0],
            'case_name': case[1],
            'case_description': case[2],
            'legal_issue': case[3],
            'incident_date': case[4],
            'service_type': case[5],
            'expected_outcome': case[6],
            'priority_level': case[7],
            'deadline': case[8],
            'case_date': case[9],
            'supporting_documents': case[10],
            'status': case[11],
            'advocate_name': case[12],  # Advocate's name
        })
    
    context = {
        'client': client_dict,
        'case_history': case_history_list,
        'adv_id': advocate_id,
    }
    
    return render(request, 'advocate/requested_client.html', context)
#-----------------------------------------feedback----------------------------------------------------------------------
import pymysql
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.db import connection

def feedback(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")
    
    # Establish MySQL connection
    conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch advocate's name for display
            cursor.execute("SELECT u_name FROM tbl_user WHERE u_id = %s", (advocate_id,))
            advocate = cursor.fetchone()
            
            if not advocate:
                return HttpResponse("Advocate not found", status=404)

            # Prepare advocate data
            advocate_data = {
                'u_id': advocate_id,
                'u_name': advocate['u_name']
            }
    finally:
        conn.close()

    return render(request, 'client/feedback.html', {'advocate': advocate_data})

def submit_feedback(request, advocate_id):
    if request.method == 'POST' and "client_id" in request.session:
        user_id = request.session['client_id']
        feedback_text = request.POST.get('feedback_text')
        rating = request.POST.get('rating')
        emoji = request.POST.get('emoji')
        created_at = timezone.now()
        
        # Insert feedback into `tbl_feedback`
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tbl_feedback (user_id, advocate_id, feedback_text, rating, emoji, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [user_id, advocate_id, feedback_text, rating, emoji, created_at])
        
        return redirect('feedback', advocate_id=advocate_id)  # Redirect to the feedback page

    return redirect('login')

#---------------------feedback-view advocate----------------------------------------------

def view_feedback(request):
    # Ensure the advocate is logged in
    if "adv_id" not in request.session:
        return redirect("login")
    
    advocate_id = request.session['adv_id']
    
    # Get filter and sort parameters from the request
    filter_client = request.GET.get('client', '').strip()  # Get client name and strip whitespace
    filter_rating = request.GET.get('rating', '')
    sort_by = request.GET.get('sort', 'created_at')  # Default sort by created_at

    print(f"Filter Client: {filter_client}")  # Debugging line
    print(f"Filter Rating: {filter_rating}")  # Debugging line
    print(f"Sort By: {sort_by}")  # Debugging line

    # Base query
    query = """
        SELECT f.feedback_text, f.rating, f.emoji, f.created_at, u.u_name 
        FROM tbl_feedback AS f
        JOIN tbl_user AS u ON f.user_id = u.u_id
        WHERE f.advocate_id = %s
    """
    params = [advocate_id]

    # Add filtering conditions
    if filter_client:
        query += " AND u.u_name LIKE %s"
        params.append(f"%{filter_client}%")  # Use LIKE for partial matches

    if filter_rating:
        query += " AND f.rating = %s"
        params.append(filter_rating)

    # Add sorting
    query += f" ORDER BY {sort_by} DESC"  # Sort by the specified field

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        feedback = cursor.fetchall()

    return render(request, 'advocate/view_feedback.html', {
        'feedback': feedback,
        'filter_client': filter_client,
        'filter_rating': filter_rating,
        'sort_by': sort_by,
    })
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.db import connection
from django.utils import timezone

def submit_feedback(request, advocate_id):
    if request.method == 'POST' and "client_id" in request.session:
        user_id = request.session['client_id']
        feedback_text = request.POST.get('feedback_text')
        rating = request.POST.get('rating')
        emoji = request.POST.get('emoji')
        created_at = timezone.now()

        # Insert feedback into `tbl_feedback`
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tbl_feedback (user_id, advocate_id, feedback_text, rating, emoji, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [user_id, advocate_id, feedback_text, rating, emoji, created_at])

        # Send notification to the advocate
        send_feedback_notification(advocate_id, feedback_text)

        return redirect('feedback', advocate_id=advocate_id)  # Redirect to the feedback page

    return redirect('login')

def send_feedback_notification(advocate_id, feedback_text):
    # Fetch advocate's email address
    with connection.cursor() as cursor:
        cursor.execute("SELECT email FROM tbl_user WHERE u_id = %s", [advocate_id])
        advocate = cursor.fetchone()

    if advocate:
        advocate_email = advocate[0]
        subject = 'New Feedback Received'
        message = f'You have received new feedback: "{feedback_text}"'
        from_email = settings.EMAIL_HOST_USER

        # Send email
        try:
            send_mail(subject, message, from_email, [advocate_email])
            print("Email sent successfully!")  # Debugging line
        except Exception as e:
            print(f"Error sending email: {e}")  # Debugging line

# home/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
import pymysql
from datetime import datetime

# Establish the database connection
conn = pymysql.connect(host="localhost", user="root", password="", database="legal_advisor")

def book_appointment(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")

    client_id = request.session.get("client_id")

    if request.method == "POST":
        appointment_date = request.POST.get("appointment_date")
        appointment_time = request.POST.get("appointment_time")

        with connection.cursor() as cursor:
            # Check advocate availability
            check_availability_query = """
                                        SELECT * FROM tbl_appointment
                                        WHERE advocate_id = %s AND appointment_date = %s AND appointment_time = %s
                                        """
            cursor.execute(check_availability_query, (advocate_id, appointment_date, appointment_time))
            availability = cursor.fetchone()

            if availability:
                return HttpResponse("This appointment slot is already booked.", status=400)

            # Insert appointment record
            insert_appointment_query = """
                                        INSERT INTO tbl_appointment (advocate_id, client_id, appointment_date, appointment_time) 
                                        VALUES (%s, %s, %s, %s)
                                        """
            cursor.execute(insert_appointment_query, (advocate_id, client_id, appointment_date, appointment_time))
            connection.commit()

            # Fetch advocate's email to notify them about the appointment
            cursor.execute("SELECT email FROM tbl_user WHERE u_id = %s", [advocate_id])
            advocate = cursor.fetchone()

            # Fetch client’s name
            cursor.execute("SELECT u_name FROM tbl_user WHERE u_id = %s", [client_id])
            client = cursor.fetchone()

            if advocate and client:
                advocate_email = advocate[0]
                client_name = client[0]
                subject = "New Appointment Booked"
                message = f"A new appointment has been booked:\n\nDate: {appointment_date}\nTime: {appointment_time}\nClient Name: {client_name}"
                from_email = settings.EMAIL_HOST_USER

                # Send email notification
                send_mail(subject, message, from_email, [advocate_email])

        return HttpResponse("Appointment booked successfully")

    context = {
        "advocate_id": advocate_id
    }
    return render(request, "client/book_appointment.html", context)

from django.utils import timezone
from django.shortcuts import render

def view_appointments(request, advocate_id):
    if "client_id" not in request.session:
        return redirect("login")

    # Store the advocate_id in the session
    request.session['advocate_id'] = advocate_id

    client_id = request.session.get("client_id")
    current_datetime = timezone.now()  # Current date and time

    with connection.cursor() as cursor:
        # Fetch upcoming appointments
        upcoming_appointments_query = """
        SELECT id, appointment_date, appointment_time
        FROM tbl_appointment
        WHERE advocate_id = %s AND client_id = %s 
        AND (appointment_date > %s OR (appointment_date = %s AND appointment_time > %s))
        ORDER BY appointment_date, appointment_time
        """
        cursor.execute(upcoming_appointments_query, 
                       (advocate_id, client_id, current_datetime.date(), current_datetime.date(), current_datetime.time()))
        upcoming_appointments = cursor.fetchall()

        # Fetch past appointments using combined datetime
        past_appointments_query = """
        SELECT id, appointment_date, appointment_time
        FROM tbl_appointment
        WHERE advocate_id = %s AND client_id = %s 
        AND TIMESTAMP(appointment_date, appointment_time) <= %s
        ORDER BY appointment_date DESC, appointment_time DESC
        """
        cursor.execute(past_appointments_query, (advocate_id, client_id, current_datetime))
        past_appointments = cursor.fetchall()

    # Convert tuples to dictionaries for better access in templates
    upcoming_appointments = [
        {'id': row[0], 'appointment_date': row[1], 'appointment_time': row[2]} for row in upcoming_appointments
    ]
    past_appointments = [
        {'id': row[0], 'appointment_date': row[1], 'appointment_time': row[2]} for row in past_appointments
    ]

    context = {
        'advocate_id': advocate_id,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'client/view_appointments.html', context)
from django.shortcuts import redirect
from django.db import connection
from django.http import HttpResponse
def cancel_appointment(request, appointment_id):
    try:
        with connection.cursor() as cursor:
            # Get appointment details
            cursor.execute("SELECT advocate_id, client_id, appointment_date, appointment_time FROM tbl_appointment WHERE id = %s", [appointment_id])
            appointment = cursor.fetchone()
            if not appointment:
                return HttpResponse("Appointment not found.")

            advocate_id, client_id, appointment_date, appointment_time = appointment

            # Update the appointment status to 'Cancelled'
            cursor.execute("UPDATE tbl_appointment SET status = 'Cancelled' WHERE id = %s", [appointment_id])
            connection.commit()

            # Fetch advocate's email and client name for notification
            cursor.execute("SELECT email FROM tbl_user WHERE u_id = %s", [advocate_id])
            advocate = cursor.fetchone()
            cursor.execute("SELECT u_name FROM tbl_user WHERE u_id = %s", [client_id])
            client = cursor.fetchone()

            if advocate and client:
                advocate_email = advocate[0]
                client_name = client[0]
                subject = "Appointment Canceled"
                message = f"An appointment has been canceled:\n\nDate: {appointment_date}\nTime: {appointment_time}\nClient Name: {client_name}"
                from_email = settings.EMAIL_HOST_USER

                # Send email notification
                send_mail(subject, message, from_email, [advocate_email])

        # Redirect back to the appointments page after cancellation
        advocate_id = request.session.get('advocate_id')  # Retrieve advocate_id from the session
        if advocate_id is None:
            return HttpResponse("Advocate ID not found in session.")
        
        return redirect('view_appointments', advocate_id=advocate_id)
    except Exception as e:
        return HttpResponse(f"Error cancelling appointment: {str(e)}")
from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from django.contrib import messages  # Add this line at the top of your file

def manage_appointments(request, advocate_id, client_id):
    current_datetime = timezone.now()

    # Fetch appointments
    with connection.cursor() as cursor:
        # Retrieve upcoming appointments
        cursor.execute("""
            SELECT id, appointment_date, appointment_time
            FROM tbl_appointment
            WHERE advocate_id = %s AND client_id = %s 
            AND TIMESTAMP(appointment_date, appointment_time) > %s
            ORDER BY appointment_date, appointment_time
        """, (advocate_id, client_id, current_datetime))
        appointments = cursor.fetchall()

    # Convert tuples to dictionaries for template access
    appointments = [
        {'id': row[0], 'appointment_date': row[1], 'appointment_time': row[2]} for row in appointments
    ]

    context = {
        'advocate_id': advocate_id,
        'client_id': client_id,
        'appointments': appointments,
    }
    return render(request, 'advocate/manage_appointment.html', context)

# Function to cancel an appointment
def cancel_appointment(request, appointment_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM tbl_appointment WHERE id = %s", [appointment_id])
    return redirect(request.META.get('HTTP_REFERER', '/'))

# Function to reschedule an appointment
def reschedule_appointment(request, appointment_id):
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tbl_appointment 
                SET appointment_date = %s, appointment_time = %s 
                WHERE id = %s
            """, (new_date, new_time, appointment_id))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return render(request, 'advocate/reschedule_appointment.html', {'appointment_id': appointment_id})
def request_reschedule_appointment(request, appointment_id):
    if request.method == 'POST':
        new_date = request.POST['new_date']
        new_time = request.POST['new_time']
        client_email = request.POST['client_email']
        advocate_id = request.POST.get('advocate_id')
        client_id = request.POST.get('client_id')

        # Send email to the client for rescheduling
        subject = 'Appointment Rescheduling Request'
        message = f'Your appointment has been requested to be rescheduled to {new_date} at {new_time}.'
        send_mail(subject, message, 'from@example.com', [client_email])

        messages.success(request, 'Reschedule request sent successfully!')
        
        # Redirect to the appointment management view with both advocate_id and client_id
        return redirect('view_appointments', advocate_id=advocate_id, client_id=client_id)