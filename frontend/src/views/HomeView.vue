<script setup>
import { ref, computed } from 'vue'
import DashboardStats from '../components/DashboardStats.vue'
import ParkingGrid from '../components/ParkingGrid.vue'

const gridRef = ref(null)

const spots = computed(() => gridRef.value?.spots || [])
const loading = computed(() => gridRef.value?.loading || false)
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
      
    </div>

    <!-- Stats Row -->
    <DashboardStats :spots="spots" :loading="loading" />

    <!-- Grid View -->
    <div class="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-200/50">
      <ParkingGrid ref="gridRef" />
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
