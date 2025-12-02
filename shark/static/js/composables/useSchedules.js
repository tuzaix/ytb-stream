const { ref, computed } = Vue;
import { api } from '../modules/api.js';
import { buildCronString, formatCron } from '../modules/utils.js';

export function useSchedules(t, showToastMessage, currentMaterials) {
    const schedulesData = ref({ items: [], total: 0, page: 1, pageSize: 10 });
    const showSchedulesModal = ref(false);
    const currentSchedules = ref([]);
    const selectedAccount = ref(null);
    const newSchedule = ref({ material_config_id: '', cron_expression: '' });
    
    // Cron Builder State
    const scheduleForm = ref({
        type: 'interval', // interval, daily, weekly, monthly
        interval: { value: 30, unit: 'minutes' },
        time: '10:00',
        weekdays: [], // 0-6
        monthDay: 1
    });

    const generateCron = computed(() => buildCronString(scheduleForm.value));

    const fetchAccountSchedules = async (accountId, selectedMaterialConfigId) => {
         if (!accountId) return;
        const skip = (schedulesData.value.page - 1) * schedulesData.value.pageSize;
        try {
            let url = `/youtube/accounts/${accountId}/schedules?skip=${skip}&limit=${schedulesData.value.pageSize}`;
            if (selectedMaterialConfigId) {
                url += `&material_config_id=${selectedMaterialConfigId}`;
            }
            const res = await api.get(url);
            schedulesData.value.items = res.data.items;
            schedulesData.value.total = res.data.total;
        } catch (e) {
            console.error(e);
        }
    };

    const openSchedules = async (acc) => {
         selectedAccount.value = acc;
         showSchedulesModal.value = true;
         try {
             const res = await api.get(`/youtube/accounts/${acc.id}/schedules?skip=0&limit=100`);
             currentSchedules.value = res.data.items;
             const matRes = await api.get(`/youtube/accounts/${acc.id}/materials?skip=0&limit=100`);
             currentMaterials.value = matRes.data.items; 
        } catch (e) {
            console.error(e);
        }
    };

    const createSchedule = async (currentAccountId, currentView) => {
        if (!selectedAccount.value && !currentAccountId) return;
        const accId = selectedAccount.value ? selectedAccount.value.id : currentAccountId;

        try {
            const { type, interval, time, weekdays, monthDay } = scheduleForm.value;
            
            const payload = {
                material_config_id: newSchedule.value.material_config_id,
                schedule_type: type,
                is_active: true
            };

            if (type === 'interval') {
                payload.interval_value = interval.value;
                payload.interval_unit = interval.unit;
            } else if (type === 'daily') {
                payload.run_time = time;
            } else if (type === 'weekly') {
                payload.run_time = time;
                payload.weekdays = weekdays.join(',');
            } else if (type === 'monthly') {
                payload.run_time = time;
                payload.month_day = monthDay;
            }

            await api.post(`/youtube/accounts/${accId}/schedules`, payload);
            
            if (currentView === 'account_details') {
                // We need to call the fetch function, but it depends on arguments.
                // The caller should handle the refresh or we pass a callback.
            } else {
                const res = await api.get(`/youtube/accounts/${accId}/schedules?skip=0&limit=100`);
                currentSchedules.value = res.data.items;
            }

            // Reset form?
            showSchedulesModal.value = false;
            showToastMessage(t('alerts.add_success') || 'Added successfully');
            return true; // Signal success
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.create_schedule_failed'));
            return false;
        }
    };

    const deleteSchedule = async (id, currentAccountId, currentView) => {
        if (!confirm(t('alerts.confirm_delete'))) return;
        const accId = selectedAccount.value ? selectedAccount.value.id : currentAccountId;

        try {
            await api.delete(`/youtube/schedules/${id}`);
            
            if (currentView === 'account_details') {
                // Signal refresh
            } else {
                const res = await api.get(`/youtube/accounts/${accId}/schedules?skip=0&limit=100`);
                currentSchedules.value = res.data.items;
            }
            showToastMessage(t('alerts.delete_success') || 'Deleted successfully');
            return true;
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.delete_failed'));
            return false;
        }
    };

    const handleSchedulesPageChange = (newPage, accountId, selectedMaterialConfigId) => {
         schedulesData.value.page = newPage;
         fetchAccountSchedules(accountId, selectedMaterialConfigId);
    };

    const handleSchedulesPageSizeChange = (accountId, selectedMaterialConfigId) => {
         schedulesData.value.page = 1;
         fetchAccountSchedules(accountId, selectedMaterialConfigId);
    };

    return {
        schedulesData,
        showSchedulesModal,
        currentSchedules,
        newSchedule,
        scheduleForm,
        generateCron,
        fetchAccountSchedules,
        openSchedules,
        createSchedule,
        deleteSchedule,
        handleSchedulesPageChange,
        handleSchedulesPageSizeChange,
        selectedAccount
    };
}
