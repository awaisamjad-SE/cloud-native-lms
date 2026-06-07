import { apiGet, apiPatch, apiPost } from "@/lib/api";

export type Id = string | number;

export const lmsApi = {
  auth: {
    register: (payload: {
      username: string;
      email: string;
      password: string;
      first_name?: string;
      last_name?: string;
    }) => apiPost("/auth/register/", payload, { auth: false }),
    login: (payload: { username: string; password: string }) =>
      apiPost<{ access?: string; refresh?: string; access_token?: string; refresh_token?: string; user?: Record<string, unknown> }>(
        "/auth/login/",
        payload,
        { auth: false },
      ),
    refreshToken: (refresh: string) => apiPost("/auth/token/refresh/", { refresh }, { auth: false }),
    getProfile: () => apiGet("/auth/profile/"),
    patchProfile: (payload: { first_name?: string; last_name?: string; phone_number?: string; bio?: string }) =>
      apiPatch("/auth/profile/", payload),
    uploadProfileImage: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return apiPost("/auth/profile/upload-image/", fd);
    },
    getProfileUploadPresigned: () => apiGet("/auth/profile/upload-image/presigned/"),
    changePassword: (payload: { old_password: string; new_password: string }) =>
      apiPost("/auth/change-password/", payload),
    adminListUsers: () => apiGet("/auth/admin/users/"),
    adminUserDetail: (userId: Id) => apiGet(`/auth/admin/users/${userId}/`),
    adminActivateUser: (userId: Id) => apiPost(`/auth/admin/users/${userId}/activate/`, {}),
    adminDeactivateUser: (userId: Id) => apiPost(`/auth/admin/users/${userId}/deactivate/`, {}),
  },

  courses: {
    list: (search?: string) =>
      apiGet(`/courses/${search ? `?search=${encodeURIComponent(search)}` : ""}`),
    detail: (slug: string) => apiGet(`/courses/${slug}/`),
    lessons: (slug: string) => apiGet(`/courses/${slug}/lessons/`),
    progress: (slug: string) => apiGet(`/courses/${slug}/progress/`),
    lessonAccess: (lessonId: Id) => apiGet(`/lessons/${lessonId}/access/`),
    completeLesson: (lessonId: Id) => apiPost(`/lessons/${lessonId}/complete/`, {}),
    adminCreate: (payload: {
      title: string;
      slug?: string;
      description: string;
      price: number;
      category: string;
      status: string;
    }) => apiPost("/admin/courses/", payload),
    adminUpdate: (courseId: Id, payload: Record<string, unknown>) =>
      apiPatch(`/admin/courses/${courseId}/`, payload),
    adminPublish: (courseId: Id) => apiPost(`/admin/courses/${courseId}/publish/`, {}),
    adminUploadThumbnail: (courseId: Id, file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return apiPost(`/admin/courses/${courseId}/thumbnail/`, fd);
    },
    adminCreateLesson: (payload: {
      course: Id;
      title: string;
      lesson_type: string;
      is_preview: boolean;
      order: number;
      duration?: number;
      file?: File | null;
    }) => {
      const fd = new FormData();
      fd.append("course", String(payload.course));
      fd.append("title", payload.title);
      fd.append("lesson_type", payload.lesson_type);
      fd.append("is_preview", String(payload.is_preview));
      fd.append("order", String(payload.order));
      if (payload.duration !== undefined) fd.append("duration", String(payload.duration));
      if (payload.file) fd.append("file", payload.file);
      return apiPost("/admin/lessons/", fd);
    },
    adminLessons: (courseId?: Id) => apiGet(`/admin/lessons/${courseId ? `?course=${courseId}` : ""}`),
  },

  enrollments: {
    my: () => apiGet("/enrollments/my/"),
    adminList: () => apiGet("/admin/enrollments/"),
    adminCreate: (payload: { student_id: Id; course_id: Id }) => apiPost("/admin/enrollments/", payload),
    adminActivate: (enrollmentId: Id) => apiPost(`/admin/enrollments/${enrollmentId}/activate/`, {}),
    adminDeactivate: (enrollmentId: Id) => apiPost(`/admin/enrollments/${enrollmentId}/deactivate/`, {}),
  },

  payments: {
    publicBankAccounts: () => apiGet("/payments/bank-accounts/"),
    submitOffline: (payload: {
      course_id: Id;
      bank_account_id: Id;
      transaction_reference: string;
      proof_note?: string;
      proof_receipt?: File | null;
    }) => {
      // If a file is provided, submit as multipart/form-data; otherwise send JSON
      if (payload.proof_receipt) {
        const fd = new FormData();
        fd.append("course_id", String(payload.course_id));
        fd.append("bank_account_id", String(payload.bank_account_id));
        fd.append("transaction_reference", payload.transaction_reference);
        if (payload.proof_note) fd.append("proof_note", payload.proof_note);
        fd.append("proof_receipt", payload.proof_receipt);
        return apiPost("/payments/offline/submit/", fd);
      }
      return apiPost("/payments/offline/submit/", {
        course_id: payload.course_id,
        bank_account_id: payload.bank_account_id,
        transaction_reference: payload.transaction_reference,
        proof_note: payload.proof_note,
      });
    },
    my: () => apiGet("/payments/my/"),
    adminList: () => apiGet("/admin/payments/"),
    adminApprove: (paymentId: Id) => apiPost(`/admin/payments/${paymentId}/approve/`, {}),
    adminReject: (paymentId: Id, rejection_reason: string) =>
      apiPost(`/admin/payments/${paymentId}/reject/`, { rejection_reason }),
    adminBankAccounts: () => apiGet("/admin/bank-accounts/"),
    adminCreateBankAccount: (payload: {
      bank_name: string;
      account_title: string;
      account_number: string;
      iban?: string;
      instructions?: string;
      is_active: boolean;
    }) => apiPost("/admin/bank-accounts/", payload),
    adminBankAccountDetail: (bankAccountId: Id) => apiGet(`/admin/bank-accounts/${bankAccountId}/`),
  },
};
