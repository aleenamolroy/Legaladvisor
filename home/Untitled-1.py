
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
    }
    return render(request, 'client/advocate_profile.html', context)