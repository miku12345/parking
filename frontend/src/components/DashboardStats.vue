<script setup>
import { computed } from 'vue'

const props = defineProps({
  spots: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const totalSpots = computed(() => props.spots.length)
const availableSpots = computed(() => props.spots.filter(s => s.status === 'free').length)
const occupiedSpots = computed(() => props.spots.filter(s => s.status === 'occupied' || s.status === 'violation').length)
const reservedSpots = computed(() => props.spots.filter(s => s.status === 'reserved').length)

</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
    
    <!-- Total Card -->
    <div class="relative overflow-hidden bg-white border border-slate-200 shadow-sm rounded-2xl p-5 hover:border-slate-300 transition-colors group">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-slate-500 text-sm font-medium">Total Spaces</h3>
        <div class="p-2 bg-slate-100 rounded-lg text-slate-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h16M4 14h16M4 6h16M4 18h16"/></svg>
        </div>
      </div>
      <div class="flex items-baseline gap-2">
        <span v-if="loading" class="h-9 w-16 bg-slate-200 animate-pulse rounded"></span>
        <span v-else class="text-3xl font-bold text-slate-900">{{ totalSpots }}</span>
      </div>
    </div>

    <!-- Available Card -->
    <div class="relative overflow-hidden bg-white border border-slate-200 shadow-sm rounded-2xl p-5 hover:border-emerald-300 transition-colors group">
      <div class="absolute inset-0 bg-emerald-50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div class="flex items-center justify-between mb-4 relative">
        <h3 class="text-slate-500 text-sm font-medium">Available</h3>
        <div class="p-2 bg-emerald-100 rounded-lg text-emerald-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
        </div>
      </div>
      <div class="flex items-baseline gap-2 relative">
        <span v-if="loading" class="h-9 w-16 bg-slate-200 animate-pulse rounded"></span>
        <span v-else class="text-3xl font-bold text-emerald-600">{{ availableSpots }}</span>
      </div>
    </div>

    <!-- Occupied Card -->
    <div class="relative overflow-hidden bg-white border border-slate-200 shadow-sm rounded-2xl p-5 hover:border-rose-300 transition-colors group">
      <div class="absolute inset-0 bg-rose-50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div class="flex items-center justify-between mb-4 relative">
        <h3 class="text-slate-500 text-sm font-medium">Occupied</h3>
        <div class="p-2 bg-rose-100 rounded-lg text-rose-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
        </div>
      </div>
      <div class="flex items-baseline gap-2 relative">
        <span v-if="loading" class="h-9 w-16 bg-slate-200 animate-pulse rounded"></span>
        <span v-else class="text-3xl font-bold text-rose-600">{{ occupiedSpots }}</span>
      </div>
    </div>

    <!-- Utilization Card -->
    <div class="relative overflow-hidden bg-white border border-slate-200 shadow-sm rounded-2xl p-5 hover:border-indigo-300 transition-colors group">
      <div class="absolute inset-0 bg-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div class="flex items-center justify-between mb-4 relative">
        <h3 class="text-slate-500 text-sm font-medium">Reserved</h3>
        <div class="p-2 bg-indigo-100 rounded-lg text-indigo-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        </div>
      </div>
      <div class="flex items-baseline gap-2 relative">
        <span v-if="loading" class="h-9 w-16 bg-slate-200 animate-pulse rounded"></span>
        <span v-else class="text-3xl font-bold text-slate-900">{{ reservedSpots }}</span>
      </div>
    </div>

  </div>
</template>
