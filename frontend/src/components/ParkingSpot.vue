<script setup>
import { computed } from 'vue'

const props = defineProps({
  spot: {
    type: Object,
    required: true,
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['view-logs'])

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
    case 'violation':
      return {
        bg: 'bg-red-50',
        border: 'border-red-300',
        text: 'text-red-700',
        shadow: 'shadow-sm hover:shadow-md hover:border-red-400',
        indicator: 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
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

function handleClick() {
  if (props.isAdmin) {
    emit('view-logs', props.spot.spot_id || props.spot.id)
  }
}
</script>

<template>
  <div 
    class="group relative flex flex-col items-center justify-center p-4 min-h-[100px] rounded-2xl border transition-all duration-300 bg-white"
    :class="[statusConfig.bg, statusConfig.border, statusConfig.shadow, isAdmin ? 'cursor-pointer hover:-translate-y-1' : '']"
    role="listitem" 
    :aria-label="`${spot.label} ${spot.status}`"
    @click="handleClick"
  >
    <!-- Status Indicator Dot and Caution Mark -->
    <div class="absolute top-3 right-3 flex items-center gap-2">
      <div class="w-2 h-2 rounded-full relative" :class="statusConfig.indicator">
        <div v-if="spot.status === 'available'" class="absolute inset-0 rounded-full animate-ping opacity-75" :class="statusConfig.indicator"></div>
      </div>
    </div>
    
    <div class="text-xl font-bold tracking-tight text-slate-900 mb-1 drop-shadow-sm">
      {{ spot.label || `${spot.spot_id || spot.id}` }}
    </div>
    
    <div 
      class=" flex items-center text-[0.65rem] uppercase tracking-wider font-semibold rounded-full px-2.5 py-0.5 border bg-white mb-2"
      :class="[statusConfig.text, statusConfig.border]"
    >
      {{ spot.status }}<span v-if="spot.status === 'violation'" class="text-[0.675rem] drop-shadow-sm animate-pulse" title="Violation">❗</span>

    </div>
    
    <!-- Current Plate Display (if occupied/reserved/violation) -->
    <div v-if="(spot.status === 'occupied' || spot.status === 'reserved' || spot.status === 'violation') && (spot.current_plate || spot.reserved_plate) && isAdmin" class="mt-auto w-full">
      <div class="px-2 py-1 text-[0.8rem] font-mono font-bold text-slate-800 border border-black-400 rounded flex justify-center uppercase tracking-widest shadow-sm whitespace-nowrap">
        {{ spot.current_plate || spot.reserved_plate}}
      </div>
    </div>
  </div>
</template>
