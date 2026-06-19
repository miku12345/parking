<script setup>
import { ref, onMounted, computed } from 'vue'

const isAuthenticated = ref(false)
const apiKey = ref('')
const loginError = ref('')

const loading = ref(false)
const seeding = ref(false)
const training = ref(false)

const selectedWeekday = ref(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1) // Default to today (0=Mon, 6=Sun)
const forecastData = ref(null)
const modelInfo = ref(null)

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

onMounted(() => {
  const savedKey = sessionStorage.getItem('admin_api_key')
  if (savedKey) {
    apiKey.value = savedKey
    login()
  }
})

async function login() {
  if (!apiKey.value.trim()) {
    loginError.value = 'Please enter an API Key'
    return
  }
  
  loginError.value = ''
  loading.value = true
  
  try {
    // Authenticate by checking anomalies, just like AdminView
    const authRes = await fetch('/api/anomalies', { headers: { 'X-API-Key': apiKey.value } })
    if (!authRes.ok) {
      throw new Error('Invalid API Key')
    }
    
    isAuthenticated.value = true
    sessionStorage.setItem('admin_api_key', apiKey.value)
    
    // Now fetch initial forecast
    await loadForecast()
  } catch (err) {
    loginError.value = err.message
    isAuthenticated.value = false
    sessionStorage.removeItem('admin_api_key')
  } finally {
    loading.value = false
  }
}

function logout() {
  isAuthenticated.value = false
  apiKey.value = ''
  forecastData.value = null
  modelInfo.value = null
  sessionStorage.removeItem('admin_api_key')
}

async function loadForecast() {
  try {
    const res = await fetch(`/api/predict/forecast?weekday=${selectedWeekday.value}`)
    const data = await res.json()
    
    if (data.ok) {
      forecastData.value = data
      modelInfo.value = { trained: true }
    } else {
      forecastData.value = null
      modelInfo.value = data.info || { trained: false, reason: data.warning }
    }
  } catch (err) {
    console.error('Failed to load forecast', err)
  }
}

async function seedData() {
  if (!confirm("Are you sure you want to seed synthetic data? This might take a moment.")) return
  
  seeding.value = true
  try {
    const res = await fetch('/api/predict/seed?days=14&lot_size=20', { method: 'POST' })
    const data = await res.json()
    console.log('Seeded:', data)
    alert('Data seeding completed!')
    await loadForecast()
  } catch (err) {
    console.error('Failed to seed', err)
    alert('Failed to seed data')
  } finally {
    seeding.value = false
  }
}

async function trainModel() {
  training.value = true
  try {
    const res = await fetch('/api/predict/train', { method: 'POST' })
    const data = await res.json()
    console.log('Trained:', data)
    alert('Model training completed! Samples: ' + data.samples)
    await loadForecast()
  } catch (err) {
    console.error('Failed to train', err)
    alert('Failed to train model')
  } finally {
    training.value = false
  }
}

function selectDay(dayIndex) {
  selectedWeekday.value = dayIndex
  loadForecast()
}

// Compute the max spots to scale the bars
const maxSpots = computed(() => {
  if (!forecastData.value || !forecastData.value.total_spots) return 20 // fallback
  return Math.max(forecastData.value.total_spots, 1)
})
</script>

<template>
  <div class="space-y-8 animate-fade-in max-w-5xl mx-auto">
    
    <!-- Login Screen -->
    <div v-if="!isAuthenticated" class="flex items-center justify-center min-h-[60vh]">
      <div class="bg-white border border-slate-200 rounded-3xl p-8 md:p-10 shadow-xl shadow-slate-200/50 max-w-md w-full">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-purple-50 text-purple-600 mb-4 border border-purple-100 shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Prediction Admin</h2>
          <p class="text-sm text-slate-500 mt-2">Enter your backend API Key to manage AI models and forecasts.</p>
        </div>
        
        <form @submit.prevent="login" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">API Key / Password</label>
            <input 
              type="password" 
              v-model="apiKey"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-shadow"
              placeholder="Enter key..."
            />
          </div>
          <div v-if="loginError" class="text-sm text-rose-600 font-medium bg-rose-50 px-3 py-2 rounded-lg border border-rose-200">
            {{ loginError }}
          </div>
          <button 
            type="submit" 
            :disabled="loading"
            class="w-full px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-70 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors shadow-md shadow-purple-200 flex justify-center items-center gap-2"
          >
            {{ loading ? 'Authenticating...' : 'Secure Login' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Admin Dashboard -->
    <div v-else class="space-y-8">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">AI Predictions</h1>
          <p class="text-slate-500 mt-2 max-w-2xl text-sm md:text-base">
            Manage the parking availability prediction model and view occupancy forecasts.
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="logout" class="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 text-sm font-medium rounded-lg transition-colors border border-rose-200 shadow-sm">
            Logout
          </button>
        </div>
      </div>

      <!-- Model Status & Actions -->
      <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-xl shadow-slate-200/50">
        <div class="flex flex-col md:flex-row items-center justify-between gap-6">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-2xl" :class="modelInfo?.trained ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'">
              <svg v-if="modelInfo?.trained" xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div>
              <h2 class="text-xl font-bold text-slate-900">
                Model Status: 
                <span v-if="modelInfo?.trained" class="text-emerald-600">Trained & Active</span>
                <span v-else class="text-amber-600">Not Trained</span>
              </h2>
              <p class="text-sm text-slate-500 mt-1" v-if="!modelInfo?.trained">
                {{ modelInfo?.reason || 'The model needs more data to provide predictions.' }}
              </p>
              <p class="text-sm text-slate-500 mt-1" v-else>
                Ready to provide hourly availability forecasts.
              </p>
            </div>
          </div>
          
          <div class="flex items-center gap-3 w-full md:w-auto">
            <button 
              @click="seedData" 
              :disabled="seeding"
              class="flex-1 md:flex-none px-4 py-2.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium rounded-xl transition-colors shadow-sm disabled:opacity-50"
            >
              {{ seeding ? 'Seeding...' : 'Seed Data' }}
            </button>
            <button 
              @click="trainModel" 
              :disabled="training"
              class="flex-1 md:flex-none px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-xl transition-colors shadow-md shadow-purple-200 disabled:opacity-50"
            >
              {{ training ? 'Training...' : 'Train Model' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Forecast Section -->
      <div v-if="modelInfo?.trained" class="bg-white border border-slate-200 rounded-3xl p-6 shadow-xl shadow-slate-200/50">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <h2 class="text-xl font-bold text-slate-900">Availability Forecast</h2>
          
          <!-- Day Selector -->
          <div class="flex p-1 bg-slate-100 rounded-xl overflow-x-auto">
            <button 
              v-for="(day, idx) in WEEKDAYS" 
              :key="idx"
              @click="selectDay(idx)"
              class="px-3 py-1.5 text-sm font-medium rounded-lg whitespace-nowrap transition-all"
              :class="selectedWeekday === idx ? 'bg-white text-purple-600 shadow-sm border border-slate-200' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'"
            >
              {{ day.slice(0, 3) }}
            </button>
          </div>
        </div>
        
        <!-- Forecast Chart -->
        <div v-if="forecastData && forecastData.forecast" class="relative pt-6 pb-2">
          <div class="flex items-end h-64 gap-1 sm:gap-2">
            <div 
              v-for="item in forecastData.forecast" 
              :key="item.hour" 
              class="relative flex-1 h-full flex flex-col justify-end group"
            >
              <!-- Tooltip -->
              <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                <div class="font-bold mb-1">{{ item.hour }}:00</div>
                <div>Free: {{ item.estimated_free_spots }} / {{ forecastData.total_spots }}</div>
                <div>Prob: {{ Math.round(item.p_free * 100) }}%</div>
                <!-- Triangle -->
                <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800"></div>
              </div>
              
              <!-- Bar background (Total Spots) -->
              <div class="w-full bg-slate-100 rounded-t-md h-full relative overflow-hidden flex flex-col justify-end border-b border-slate-200">
                <!-- Bar fill (Free Spots) -->
                <div 
                  class="w-full rounded-t-md transition-all duration-700 ease-out"
                  :class="item.p_free < 0.2 ? 'bg-rose-400' : (item.p_free < 0.5 ? 'bg-amber-400' : 'bg-emerald-400')"
                  :style="{ height: `${item.p_free * 100}%` }"
                ></div>
              </div>
              
              <!-- X-Axis Label -->
              <div class="text-[10px] sm:text-xs text-slate-400 text-center mt-2 font-mono">
                {{ item.hour }}h
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="forecastData && !forecastData.forecast" class="py-12 text-center text-slate-500">
          Loading forecast...
        </div>
      </div>
      
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
