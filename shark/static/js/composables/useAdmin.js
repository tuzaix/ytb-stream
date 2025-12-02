const { ref } = Vue;
import { api } from '../modules/api.js';

export function useAdmin() {
    const allUsers = ref([]);
    const showEditUserModal = ref(false);
    const editingUser = ref(null);
    const editUserForm = ref({});

    const fetchAllUsers = async () => {
        try {
            const res = await api.get('/admin/users');
            allUsers.value = res.data;
        } catch (e) {
            console.error("Failed to fetch users", e);
        }
    };

    const openEditUser = (u) => {
        editingUser.value = u;
        editUserForm.value = {
            role: u.role,
            is_active: u.is_active,
            membership_level_code: u.membership ? u.membership.level_code : 'normal'
        };
        showEditUserModal.value = true;
    };

    const saveUser = async () => {
        if (!editingUser.value) return;
        try {
            await api.put(`/admin/users/${editingUser.value.id}`, editUserForm.value);
            alert('User updated successfully');
            showEditUserModal.value = false;
            fetchAllUsers();
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to update user');
        }
    };

    return {
        allUsers,
        showEditUserModal,
        editingUser,
        editUserForm,
        fetchAllUsers,
        openEditUser,
        saveUser
    };
}
