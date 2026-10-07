from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model, login
from django.db.models import Q
from .serializers import *
from .permissions import role
from employeeApp.models import department_model, employee_model, team_model
from attendance.models import Attendance
from leave.models import LeaveRequest
from notification.models import Notification
from notification.views import create_notification

User=get_user_model()

def profile(user):
    return employee_model.objects.filter(user=user).first() or employee_model.objects.filter(email__iexact=user.email).first()

def team_members(manager):
    return employee_model.objects.filter(teams__manager=manager).distinct()

class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        # Mirrors account.views.register_view: create the account only.
        # No tokens are issued here — the client must call /auth/login/
        # afterwards, exactly like the normal Django register -> login flow.
        ser=RegistrationSerializer(data=request.data); ser.is_valid(raise_exception=True); user=ser.save()
        return Response({"detail":"Registration successful. Please log in.","user":UserSerializer(user).data},status=201)

class LoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        user=authenticate(email=request.data.get("email",""), password=request.data.get("password",""))
        if not user or not user.is_active: return Response({"detail":"Invalid email/password or inactive account."},status=401)
        refresh=RefreshToken.for_user(user)
        return Response({"user":UserSerializer(user).data,"refresh":str(refresh),"access":str(refresh.access_token)})

class FirebaseLoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        try:
            import firebase_admin
            from firebase_admin import credentials, auth
            if not firebase_admin._apps:
                import os, json
                raw=os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if not raw: return Response({"detail":"Configure FIREBASE_SERVICE_ACCOUNT_JSON on backend."},status=503)
                firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
            decoded=auth.verify_id_token(request.data.get("id_token"))
            email=decoded.get("email")
            if not email: return Response({"detail":"Firebase token has no email."},status=400)
            user,created=User.objects.get_or_create(email=email,defaults={"name":decoded.get("name") or email.split("@")[0],"is_active":True,"role":"EMPLOYEE"})
            if created: employee_model.objects.create(user=user,name=user.name,email=email,role="EMPLOYEE")
            # Create a normal Django session so @login_required views work.
            login(request, user)

            refresh=RefreshToken.for_user(user)
            return Response({"user":UserSerializer(user).data,"refresh":str(refresh),"access":str(refresh.access_token),"role":user.role})
        except Exception as exc:
            return Response({"detail":f"Firebase authentication failed: {exc}"},status=401)

class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        # Mirrors account.views.register_view: create the account only.
        # No tokens are issued here — the client must call /auth/login/
        # afterwards, exactly like the normal Django register -> login flow.
        ser=RegistrationSerializer(data=request.data); ser.is_valid(raise_exception=True); user=ser.save()
        return Response({"detail":"Registration successful. Please log in.","user":UserSerializer(user).data},status=201)

class LoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        user=authenticate(email=request.data.get("email",""), password=request.data.get("password",""))
        if not user or not user.is_active: return Response({"detail":"Invalid email/password or inactive account."},status=401)
        refresh=RefreshToken.for_user(user)
        return Response({"user":UserSerializer(user).data,"refresh":str(refresh),"access":str(refresh.access_token)})

class FirebaseLoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        try:
            import firebase_admin
            from firebase_admin import credentials, auth
            if not firebase_admin._apps:
                import os, json
                raw=os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if not raw: return Response({"detail":"Configure FIREBASE_SERVICE_ACCOUNT_JSON on backend."},status=503)
                firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
            decoded=auth.verify_id_token(request.data.get("id_token"))
            email=decoded.get("email")
            if not email: return Response({"detail":"Firebase token has no email."},status=400)
            user,created=User.objects.get_or_create(email=email,defaults={"name":decoded.get("name") or email.split("@")[0],"is_active":True,"role":"EMPLOYEE"})
            if created: employee_model.objects.create(user=user,name=user.name,email=email,role="EMPLOYEE")
            # Create a normal Django session so @login_required views work.
            login(request, user)

            refresh=RefreshToken.for_user(user)
            return Response({"user":UserSerializer(user).data,"refresh":str(refresh),"access":str(refresh.access_token),"role":user.role})
        except Exception as exc:
            return Response({"detail":f"Firebase authentication failed: {exc}"},status=401)


class ScopedAPIView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None

    def base_queryset(self):
        return self.model.objects.all()

    def get_queryset(self):
        qs = self.base_queryset()
        r = role(self.request.user)
        p = profile(self.request.user)

        if r == "HR" or self.request.user.is_superuser:
            return qs

        if self.model is employee_model:
            if r == "MANAGER" and p:
                return qs.filter(
                    Q(pk=p.pk) | Q(teams__manager=p)
                ).distinct()
            if r == "EMPLOYEE" and p:
                return qs.filter(pk=p.pk)
            return qs.none()

        if self.model is Attendance:
            if r == "MANAGER" and p:
                return qs.filter(
                    Q(employee=p) | Q(employee__teams__manager=p)
                ).distinct()
            if r == "EMPLOYEE" and p:
                return qs.filter(employee=p)
            return qs.none()

        if self.model is LeaveRequest:
            if r == "MANAGER" and p:
                return qs.filter(manager=p)
            if r == "EMPLOYEE" and p:
                return qs.filter(employee=p)
            return qs.none()

        if self.model is team_model:
            if r == "MANAGER" and p:
                return qs.filter(manager=p)
            return qs.none()

        return qs.none()

    def is_hr(self):
        return role(self.request.user) == "HR" or self.request.user.is_superuser

    def get(self, request, pk=None):
        qs = self.get_queryset()
        obj = get_object_or_404(qs, pk=pk) if pk is not None else qs
        return Response(self.serializer_class(obj, many=pk is None).data)

    def post(self, request):
        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(self.serializer_class(obj).data, status=201)

    def put(self, request, pk):
        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(self.serializer_class(obj).data)

    def patch(self, request, pk):
        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(self.serializer_class(obj).data)

    def delete(self, request, pk):
        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        obj.delete()
        return Response(status=204)


class DepartmentAPIView(ScopedAPIView):
    model = department_model
    serializer_class = DepartmentSerializer


class EmployeeAPIView(ScopedAPIView):
    model = employee_model
    serializer_class = EmployeeSerializer


class TeamAPIView(ScopedAPIView):
    model = team_model
    serializer_class = TeamSerializer

    def post(self, request):
        if role(request.user) != "MANAGER":
            return Response({"detail": "Only managers can create teams."}, status=403)
        manager = profile(request.user)
        if not manager:
            return Response({"detail": "Manager profile not found."}, status=400)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save(manager=manager)

        member_ids = request.data.get("members", [])
        if isinstance(member_ids, str):
            member_ids = [member_ids]
        members = employee_model.objects.filter(pk__in=member_ids).exclude(pk=manager.pk)
        team.members.set(members)
        members.update(manager=manager)

        for member in members:
            create_notification(
                recipient=member,
                message=f"You have been added to the {team.name} team.",
                notification_type="TEAM_ADDED",
            )
        return Response(self.serializer_class(team).data, status=201)

    def _owned_team(self, request, pk):
        manager = profile(request.user)
        return get_object_or_404(team_model, pk=pk, manager=manager)

    def put(self, request, pk):
        if role(request.user) != "MANAGER":
            return Response({"detail": "Only managers can update teams."}, status=403)
        team = self._owned_team(request, pk)
        serializer = self.serializer_class(team, data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save(manager=team.manager)
        return Response(self.serializer_class(team).data)

    def patch(self, request, pk):
        if role(request.user) != "MANAGER":
            return Response({"detail": "Only managers can update teams."}, status=403)
        team = self._owned_team(request, pk)
        serializer = self.serializer_class(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        team = serializer.save(manager=team.manager)
        return Response(self.serializer_class(team).data)

    def delete(self, request, pk):
        if role(request.user) != "MANAGER":
            return Response({"detail": "Only managers can delete teams."}, status=403)
        team = self._owned_team(request, pk)
        team.delete()
        return Response(status=204)


class TeamMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _manager_team(self, request, pk):
        if role(request.user) != "MANAGER":
            return None
        return get_object_or_404(team_model, pk=pk, manager=profile(request.user))

    def post(self, request, pk):
        team = self._manager_team(request, pk)
        if not team:
            return Response({"detail": "Only the team manager can add members."}, status=403)
        employee = get_object_or_404(employee_model, pk=request.data.get("employee_id"))
        manager = profile(request.user)
        if employee.pk == manager.pk:
            return Response({"detail": "A manager cannot add themselves as a team member."}, status=400)
        team.members.add(employee)
        employee.manager = manager
        employee.save(update_fields=["manager"])
        create_notification(
            recipient=employee,
            message=f"Your manager added you to the {team.name} team.",
            notification_type="TEAM_ADDED",
        )
        return Response(TeamSerializer(team).data, status=200)

    def delete(self, request, pk, employee_id):
        team = self._manager_team(request, pk)
        if not team:
            return Response({"detail": "Only the team manager can remove members."}, status=403)
        employee = get_object_or_404(team.members, pk=employee_id)
        manager = profile(request.user)
        team.members.remove(employee)
        if employee.manager_id == manager.id and not employee.teams.filter(manager=manager).exists():
            employee.manager = None
            employee.save(update_fields=["manager"])
        create_notification(
            recipient=employee,
            message=f"You have been removed from the {team.name} team.",
            notification_type="TEAM_REMOVED",
        )
        return Response(status=204)


class AttendanceAPIView(ScopedAPIView):
    model = Attendance
    serializer_class = AttendanceSerializer

    def post(self, request):
        r = role(request.user)
        employee = profile(request.user)
        if r not in ("HR", "MANAGER", "EMPLOYEE") or not employee:
            return Response({"detail": "Employee profile not found or access denied."}, status=403)

        # HR's manual-marking flow uses the submitted form fields.
        if r == "HR" and any(k in request.data for k in ("employee", "date", "status")):
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            return Response(self.serializer_class(obj).data, status=201)

        today = timezone.localdate()
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={"status": "Present", "check_in": timezone.localtime().time()},
        )
        if created:
            if employee.manager:
                create_notification(
                    recipient=employee.manager,
                    message=f"{employee.name} checked in.",
                    notification_type="CHECK_IN",
                )
            return Response(self.serializer_class(attendance).data, status=201)
        if attendance.check_in:
            return Response({"detail": "You have already checked in today."}, status=400)
        attendance.check_in = timezone.localtime().time()
        attendance.status = "Present"
        attendance.save(update_fields=["check_in", "status", "updated_at"])
        return Response(self.serializer_class(attendance).data)

    def patch(self, request, pk=None):
        if request.data.get("action") == "check_out":
            employee = profile(request.user)
            attendance = get_object_or_404(Attendance, pk=pk, employee=employee)
            if not attendance.check_in:
                return Response({"detail": "Please check in first."}, status=400)
            if attendance.check_out:
                return Response({"detail": "You have already checked out today."}, status=400)
            attendance.check_out = timezone.localtime().time()
            attendance.save(update_fields=["check_out", "updated_at"])
            if employee.manager:
                create_notification(recipient=employee.manager, message=f"{employee.name} checked out.", notification_type="CHECK_OUT")
            return Response(self.serializer_class(attendance).data)

        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        attendance = get_object_or_404(Attendance, pk=pk)
        serializer = self.serializer_class(attendance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(self.serializer_class(serializer.save()).data)

    def put(self, request, pk):
        if not self.is_hr():
            return Response({"detail": "HR permission required."}, status=403)
        attendance = get_object_or_404(Attendance, pk=pk)
        serializer = self.serializer_class(attendance, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(self.serializer_class(serializer.save()).data)


class LeaveRequestAPIView(ScopedAPIView):
    model = LeaveRequest
    serializer_class = LeaveRequestSerializer

    def post(self, request):
        if role(request.user) != "EMPLOYEE":
            return Response({"detail": "Only employees can submit leave requests."}, status=403)
        employee = profile(request.user)
        if not employee:
            return Response({"detail": "Employee profile not found."}, status=400)
        if not employee.manager:
            return Response({"detail": "You do not have a manager assigned yet. Please contact HR or your team manager."}, status=400)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data["start_date"]
        end = serializer.validated_data["end_date"]
        if LeaveRequest.objects.filter(
            employee=employee,
            status__in=["PENDING", "APPROVED"],
            start_date__lte=end,
            end_date__gte=start,
        ).exists():
            raise serializers.ValidationError({"detail": "You already have a pending or approved leave overlapping these dates."})

        leave = serializer.save(employee=employee, manager=employee.manager, status="PENDING")
        create_notification(recipient=employee.manager, message=f"{employee.name} submitted a leave request from {start} to {end}.", notification_type="LEAVE_SUBMITTED")
        create_notification(recipient=employee, message=f"Your leave request has been sent to {employee.manager.name}.", notification_type="LEAVE_SUBMITTED")
        return Response(self.serializer_class(leave).data, status=201)

    def _review(self, request, pk, new_status):
        if role(request.user) != "MANAGER":
            return Response({"detail": "Only the respective manager can review leave requests."}, status=403)
        manager = profile(request.user)
        leave = get_object_or_404(LeaveRequest, pk=pk, manager=manager)
        if leave.status != "PENDING":
            return Response({"detail": "This leave request has already been reviewed."}, status=400)
        leave.status = new_status
        leave.reviewed_at = timezone.now()
        leave.manager_comment = request.data.get("manager_comment", "").strip()
        leave.save(update_fields=["status", "reviewed_at", "manager_comment"])
        notification_type = "LEAVE_APPROVED" if new_status == "APPROVED" else "LEAVE_REJECTED"
        verb = "approved" if new_status == "APPROVED" else "rejected"
        create_notification(recipient=leave.employee, message=f"{manager.name} {verb} your leave request from {leave.start_date} to {leave.end_date}.", notification_type=notification_type)
        create_notification(recipient=manager, message=f"You {verb} the leave request of {leave.employee.name}.", notification_type=notification_type)
        return Response(self.serializer_class(leave).data)

    def patch(self, request, pk=None):
        action = request.data.get("action")
        if action not in ("approve", "reject"):
            return Response({"detail": "Provide action as 'approve' or 'reject'."}, status=400)
        return self._review(request, pk, "APPROVED" if action == "approve" else "REJECTED")

    def put(self, request, pk):
        return self.patch(request, pk)


class NotificationAPIView(ScopedAPIView):
    model = Notification
    serializer_class = NotificationSerializer

    def get_queryset(self):
        employee = profile(self.request.user)
        return Notification.objects.filter(recipient=employee) if employee else Notification.objects.none()

    def patch(self, request, pk=None):
        employee = profile(request.user)
        notification = get_object_or_404(Notification, pk=pk, recipient=employee)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.serializer_class(notification).data)

    def put(self, request, pk=None):
        return self.patch(request, pk)


class HRDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if role(request.user) != "HR" and not request.user.is_superuser:
            return Response({"detail": "HR permission required."}, status=403)
        return Response({
            "employees": employee_model.objects.count(),
            "active_employees": employee_model.objects.filter(status=True).count(),
            "attendance_today": Attendance.objects.filter(date=timezone.localdate()).count(),
            "pending_leave_requests": LeaveRequest.objects.filter(status="PENDING").count(),
            "recent_leave_requests": LeaveRequestSerializer(
                LeaveRequest.objects.select_related("employee", "manager")[:10], many=True
            ).data,
            "recent_notifications": NotificationSerializer(
                Notification.objects.select_related("recipient")[:10], many=True
            ).data,
        })
