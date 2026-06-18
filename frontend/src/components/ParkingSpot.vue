<script setup>
import { computed } from 'vue'

const props = defineProps({
  spot: {
    type: Object,
    required: true,
  },
})

const statusConfig = computed(() => {
  switch (props.spot.status) {
    case 'available':
      return {
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        text: 'text-emerald-700',
        shadow: 'shadow-sm hover:shadow-md hover:border-emerald-300',
        indicator: 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
      }
    case 'occupied':
      return {
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        text: 'text-rose-700',
        shadow: 'shadow-sm hover:shadow-md hover:border-rose-300',
        indicator: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]'
      }
    case 'reserved':
      return {
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-700',
        shadow: 'shadow-sm hover:shadow-md hover:border-amber-300',
        indicator: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]'
      }
    default:
      return {
        bg: 'bg-slate-50',
        border: 'border-slate-200 border-dashed',
        text: 'text-slate-500',
        shadow: '',
        indicator: 'bg-slate-400'
      }
  }
})

</script>

<template>
  <div 
    class="group relative flex flex-col items-center justify-center p-4 min-h-[100px] rounded-2xl border transition-all duration-300 hover:-translate-y-1 bg-white"
    :class="[statusConfig.bg, statusConfig.border, statusConfig.shadow]"
    role="listitem" 
    :aria-label="`${spot.label} ${spot.status}`"
  >
    <!-- Status Indicator Dot -->
    <div class="absolute top-3 right-3 w-2 h-2 rounded-full" :class="statusConfig.indicator">
      <div v-if="spot.status === 'available'" class="absolute inset-0 rounded-full animate-ping opacity-75" :class="statusConfig.indicator"></div>
    </div>
    
    <div class="text-xl font-bold tracking-tight text-slate-900 mb-1 drop-shadow-sm">
      {{ spot.label || `${spot.spot_id}` }}
    </div>
    
    <div 
      class="text-[0.65rem] uppercase tracking-wider font-semibold rounded-full px-2.5 py-0.5 border bg-white"
      :class="[statusConfig.text, statusConfig.border]"
    >
      {{ spot.status }}
    </div>
  </div>
</template>
