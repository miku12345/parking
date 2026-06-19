<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ParkingSpot from './ParkingSpot.vue'

const props = defineProps({
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['view-logs'])

const spots = ref([])
const loading = ref(true)
const error = ref(null)
let refreshInterval = null

async function fetchSpots() {
  try {
    const res = await fetch('/api/spots')
    if (!res.ok) throw new Error(`Network response not ok: ${res.status}`)
    const data = await res.json()
    spots.value = Array.isArray(data) ? data : []
    error.value = null
  } catch (err) {
    error.value = String(err.message || err)
    // Fallback sample data if backend is unreachable
    if (spots.value.length === 0) {
      spots.value = Array.from({ length: 24 }, (_, i) => {
        const status = ['available', 'occupied', 'reserved'][Math.floor(Math.random() * 3)]
        return {
          id: i + 1,
          label: `A${(i + 1).toString().padStart(2, '0')}`,
          status: status,
          current_plate: status === 'occupied' || status === 'reserved' ? `ABC-${1000 + i}` : null
        }
      })
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSpots()
  // Poll every 5 seconds for live updates
  refreshInterval = setInterval(fetchSpots, 5000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

// Expose spots and loading state to parent (HomeView) so it can pass to DashboardStats
defineExpose({ spots, loading })
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight">Live Status Map</h2>
        <p class="text-sm text-slate-500 mt-1">Real-time status of all parking spaces</p>
      </div>
      
      <div class="flex items-center gap-3">
        <div v-if="error" class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-50 border border-rose-200 text-rose-600 text-xs font-medium shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Backend offline
        </div>
        <div v-else class="">

        </div>
      </div>
    </div>

    <div v-if="loading && spots.length === 0" class="min-h-[300px] flex items-center justify-center border border-slate-300 border-dashed rounded-2xl bg-slate-50">
      <div class="flex flex-col items-center gap-3 text-slate-500">
        <svg class="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="text-sm font-medium">Connecting to sensor network...</span>
      </div>
    </div>
    
    <div v-else class="max-h-[380px] overflow-y-auto pr-2 custom-scrollbar">
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4" role="list">
        <ParkingSpot v-for="s in spots" :key="s.id" :spot="s" :isAdmin="isAdmin" @view-logs="emit('view-logs', $event)" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
