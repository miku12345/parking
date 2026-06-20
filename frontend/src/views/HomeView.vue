<script setup>
import { ref, computed, onMounted } from 'vue'
import DashboardStats from '../components/DashboardStats.vue'
import ParkingGrid from '../components/ParkingGrid.vue'

const gridRef = ref(null)
const showReserveModal = ref(false)
const reserveForm = ref({ spot_id: '', reserved_plate: '' })
const isReserving = ref(false)
const reserveError = ref('')
const reserveSuccess = ref('')
const hasAdminKey = ref(false)

const spots = computed(() => gridRef.value?.spots || [])
const availableSpots = computed(() => spots.value.filter(s => s.status === 'available' || s.status === 'free'))
const loading = computed(() => gridRef.value?.loading || false)

onMounted(() => {
  hasAdminKey.value = !!sessionStorage.getItem('admin_api_key')
})

function openModal() {
  showReserveModal.value = true
  reserveForm.value = { spot_id: '', reserved_plate: '' }
  reserveError.value = ''
  reserveSuccess.value = ''
}

async function submitReservation() {
  if (!reserveForm.value.spot_id || !reserveForm.value.reserved_plate) {
    reserveError.value = 'Please select a spot and enter your plate number.'
    return
  }
  
  isReserving.value = true
  reserveError.value = ''
  
  try {
    const apiKey = sessionStorage.getItem("admin_api_key")
    const res = await fetch('/api/reserve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json','X-API-Key': apiKey },
      body: JSON.stringify({
        spot_id: String(reserveForm.value.spot_id),
        reserved_plate: reserveForm.value.reserved_plate
      })
    })
    
    if (!res.ok) throw new Error('Failed to reserve spot.')
    
    const data = await res.json()
    if (!data.ok) throw new Error(data.warning || 'Failed to reserve spot.')
    
    reserveSuccess.value = 'Spot reserved successfully!'
    setTimeout(() => {
      showReserveModal.value = false
    }, 2000)
    
  } catch (err) {
    reserveError.value = err.message
  } finally {
    isReserving.value = false
  }
}
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-slate-200">
      <div>
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-xs font-semibold tracking-wide uppercase mb-3 shadow-sm">
          <span class="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]"></span>
          Operations Center
        </div>
        <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">Parking Spot Overview</h1>
        <p class="text-slate-500 mt-2 max-w-2xl text-sm md:text-base">
          Find an available parking spot easily. 
        </p>
      </div>
      
      <div v-if="hasAdminKey" class="flex items-center gap-3">
        <button @click="openModal" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold tracking-wide rounded-xl transition-all shadow-lg shadow-indigo-200/50 hover:shadow-indigo-300/50 hover:-translate-y-0.5 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          Reserve Spot
        </button>
      </div>
    </div>

    <!-- Stats Row -->
    <DashboardStats :spots="spots" :loading="loading" />

    <!-- Grid View -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-200/50">
      <ParkingGrid ref="gridRef" />
    </div>

    <!-- Reservation Modal -->
    <div v-if="showReserveModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="!isReserving && (showReserveModal = false)"></div>
      
      <!-- Modal Content -->
      <div class="relative bg-white rounded-3xl p-6 md:p-8 w-full max-w-md shadow-2xl animate-fade-in border border-slate-100">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-slate-900">Reserve a Spot</h2>
          <button @click="!isReserving && (showReserveModal = false)" class="text-slate-400 hover:text-slate-600 transition-colors p-2 rounded-full hover:bg-slate-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        
        <div v-if="availableSpots.length === 0" class="text-center py-8">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-rose-50 text-rose-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <h3 class="text-lg font-bold text-slate-900">Facility Full</h3>
          <p class="text-slate-500 mt-2">There are currently no available spots to reserve.</p>
        </div>
        
        <form v-else @submit.prevent="submitReservation" class="space-y-5">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">Select Spot</label>
            <select v-model="reserveForm.spot_id" class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow">
              <option value="" disabled>Choose an available spot...</option>
              <option v-for="spot in availableSpots" :key="spot.id" :value="spot.spot_id || spot.id">
                Spot {{ spot.label || (spot.spot_id || spot.id) }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">License Plate</label>
            <input v-model="reserveForm.reserved_plate" type="text" placeholder="e.g. ABC-1234" class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow uppercase" />
          </div>
          
          <div v-if="reserveError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium rounded-lg flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ reserveError }}
          </div>
          <div v-if="reserveSuccess" class="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium rounded-lg flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            {{ reserveSuccess }}
          </div>
          
          <button type="submit" :disabled="isReserving || reserveSuccess !== ''" class="w-full px-5 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-sm font-bold tracking-wide rounded-xl transition-all shadow-md flex justify-center items-center gap-2">
            <svg v-if="isReserving" class="animate-spin w-5 h-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            {{ isReserving ? 'Confirming...' : (reserveSuccess ? 'Confirmed' : 'Confirm Reservation') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
