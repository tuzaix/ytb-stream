const { ref } = Vue;
import { api } from '../modules/api.js';

export function useMaterials(t, showToastMessage, fetchAccountSchedulesCallback) {
    const materialsData = ref({ items: [], total: 0, page: 1, pageSize: 5 });
    const showMaterialsModal = ref(false);
    const selectedAccount = ref(null); // Used when opening from accounts list
    const currentMaterials = ref([]); // Used for modal list
    const newMaterial = ref({ group_name: '', material_type: 'shorts', title_template: '', description_template: '', tags: '' });
    const selectedMaterialConfigId = ref(null);

    const fetchAccountMaterials = async (accountId) => {
        if (!accountId) return;
        const skip = (materialsData.value.page - 1) * materialsData.value.pageSize;
        try {
            const res = await api.get(`/youtube/accounts/${accountId}/materials?skip=${skip}&limit=${materialsData.value.pageSize}`);
            materialsData.value.items = res.data.items;
            materialsData.value.total = res.data.total;
        } catch (e) {
            console.error(e);
        }
    };

    const openMaterials = async (acc) => {
         selectedAccount.value = acc;
         showMaterialsModal.value = true;
         try {
             const res = await api.get(`/youtube/accounts/${acc.id}/materials?skip=0&limit=100`);
             currentMaterials.value = res.data.items;
        } catch (e) {
            console.error(e);
        }
    };

    const createMaterial = async (currentAccountId) => {
        const accId = selectedAccount.value ? selectedAccount.value.id : currentAccountId;
        if (!accId) return;

        try {
            await api.post(`/youtube/accounts/${accId}/materials`, newMaterial.value);
            
            // Refresh lists
            if (currentAccountId) {
                await fetchAccountMaterials(currentAccountId);
            }
            
            // Close modal after success
            showMaterialsModal.value = false;
            
            // Clear form
            newMaterial.value = { group_name: '', material_type: 'shorts', title_template: '', description_template: '', tags: '' };
            
            showToastMessage(t('alerts.add_success'));
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.add_material_failed'));
        }
    };

    const deleteMaterial = async (id, currentAccountId) => {
        if (!confirm(t('alerts.delete_material_confirm'))) return;
        
        try {
            await api.delete(`/youtube/materials/${id}`);
            // Refresh lists
            if (currentAccountId) {
                await fetchAccountMaterials(currentAccountId);
            }
            if (selectedAccount.value) {
                 const res = await api.get(`/youtube/accounts/${selectedAccount.value.id}/materials?skip=0&limit=100`);
                 currentMaterials.value = res.data.items;
            }
            showToastMessage(t('alerts.delete_success'));
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.delete_failed'));
        }
    };

    const handleMaterialsPageChange = (newPage, currentAccountId) => {
        materialsData.value.page = newPage;
        fetchAccountMaterials(currentAccountId);
    };

    const handleMaterialsPageSizeChange = (currentAccountId) => {
         materialsData.value.page = 1;
         fetchAccountMaterials(currentAccountId);
    };

    return {
        materialsData,
        showMaterialsModal,
        selectedAccount,
        currentMaterials,
        newMaterial,
        selectedMaterialConfigId,
        fetchAccountMaterials,
        openMaterials,
        createMaterial,
        deleteMaterial,
        handleMaterialsPageChange,
        handleMaterialsPageSizeChange
    };
}
