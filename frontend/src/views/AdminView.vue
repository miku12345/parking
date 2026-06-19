<script setup>
import { ref, onMounted, computed } from 'vue'
import ParkingGrid from '../components/ParkingGrid.vue'

const gridRef = ref(null)
const isAuthenticated = ref(false)
const apiKey = ref('')
const loginError = ref('')

const logs = ref([])
const anomalies = ref([])
const reservations = ref([])
const loading = ref(false)
const selectedSpotId = ref(null)

const filteredLogs = computed(() => {
  if (!selectedSpotId.value) return logs.value
  return logs.value.filter(l => String(l.spot_id) === String(selectedSpotId.value))
})

const logPage = ref(1)
const logsPerPage = 10

const paginatedLogs = computed(() => {
  const start = (logPage.value - 1) * logsPerPage
  return filteredLogs.value.slice(start, start + logsPerPage)
})

const totalLogPages = computed(() => {
  return Math.ceil(filteredLogs.value.length / logsPerPage) || 1
})

function prevLogPage() {
  if (logPage.value > 1) logPage.value--
}

function nextLogPage() {
  if (logPage.value < totalLogPages.value) logPage.value++
}

const anomalyPage = ref(1)
const anomaliesPerPage = 5

const paginatedAnomalies = computed(() => {
  const start = (anomalyPage.value - 1) * anomaliesPerPage
  return anomalies.value.slice(start, start + anomaliesPerPage)
})

const totalAnomalyPages = computed(() => {
  return Math.ceil(anomalies.value.length / anomaliesPerPage) || 1
})

function prevAnomalyPage() {
  if (anomalyPage.value > 1) anomalyPage.value--
}

function nextAnomalyPage() {
  if (anomalyPage.value < totalAnomalyPages.value) anomalyPage.value++
}

async function fetchLogs(spotId = null) {
  try {
    const url = spotId ? `/api/logs?spot_id=${spotId}&limit=50` : '/api/logs?limit=50'
    const res = await fetch(url, { headers: { 'X-API-Key': apiKey.value } })
    if (res.ok) {
      const data = await res.json()
      logs.value = data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      logPage.value = 1
    }
  } catch (err) {
    console.error('Failed to fetch logs', err)
  }
}

async function handleViewLogs(spotId) {
  selectedSpotId.value = spotId
  await fetchLogs(spotId)
  setTimeout(() => {
    document.getElementById('logs-section')?.scrollIntoView({ behavior: 'smooth' })
  }, 100)
}

function clearLogFilter() {
  selectedSpotId.value = null
  fetchLogs()
}

onMounted(() => {
  const savedKey = sessionStorage.getItem('admin_api_key')
  if (savedKey) {
    apiKey.value = savedKey
    login()
  }
})

async function login() {
  isAuthenticated.value = true
  loading.value = false

  if (!apiKey.value.trim()) {
    loginError.value = 'Please enter an API Key'
    return
  }
  
  loginError.value = ''
  loading.value = true
  
  try {
    // Attempt to fetch data with the provided key to verify
    const [anomRes, resRes, logsRes] = await Promise.all([
      fetch('/api/anomalies', { headers: { 'X-API-Key': apiKey.value } }),
      fetch('/api/reservations', { headers: { 'X-API-Key': apiKey.value } }),
      fetch('/api/logs?limit=50', { headers: { 'X-API-Key': apiKey.value } })
    ])
    
    if (!anomRes.ok || !resRes.ok || !logsRes.ok) {
      if (anomRes.status === 401 || resRes.status === 401 || logsRes.status === 401) {
        throw new Error('Invalid API Key')
      }
      throw new Error('Failed to fetch admin data')
    }
    
    const anomaliesData = await anomRes.json()
    const reservationsData = await resRes.json()
    const logsData = await logsRes.json()
    
    anomalies.value = anomaliesData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    reservations.value = reservationsData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    logs.value = logsData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    
    isAuthenticated.value = true
    sessionStorage.setItem('admin_api_key', apiKey.value)
    
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
  logs.value = []
  anomalies.value = []
  anomalyPage.value = 1
  reservations.value = []
  sessionStorage.removeItem('admin_api_key')
}

function formatDate(isoString) {
  if (!isoString) return 'N/A'
  const date = new Date(isoString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).format(date)
}
</script>

<template>
  <div class="space-y-8 animate-fade-in max-w-5xl mx-auto">
    
    <!-- Login Screen -->
    <div v-if="!isAuthenticated" class="flex items-center justify-center min-h-[60vh]">
      <div class="bg-white border border-slate-200 rounded-3xl p-8 md:p-10 shadow-xl shadow-slate-200/50 max-w-md w-full">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-rose-50 text-rose-600 mb-4 border border-rose-100 shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Admin Authentication</h2>
          <p class="text-sm text-slate-500 mt-2">Enter your backend API Key to view sensitive logs and system anomalies.</p>
        </div>
        
        <form @submit.prevent="login" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">API Key / Password</label>
            <input 
              type="password" 
              v-model="apiKey"
              class="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow"
              placeholder="Enter key..."
            />
          </div>
          <div v-if="loginError" class="text-sm text-rose-600 font-medium bg-rose-50 px-3 py-2 rounded-lg border border-rose-200">
            {{ loginError }}
          </div>
          <button 
            type="submit" 
            :disabled="loading"
            class="w-full px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-70 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors shadow-md shadow-indigo-200 flex justify-center items-center gap-2"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
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
          <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">System Logs & Anomalies</h1>
          <p class="text-slate-500 mt-2 max-w-2xl text-sm md:text-base">
            Secure admin view for tracking detailed historical data and error events.
          </p>
        </div>
        <div class="flex items-center gap-3">
                      <RouterLink 
              to="/admin/prediction" 
              class="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg transition-colors border border-slate-200 shadow-sm flex items-center gap-2"
              exact-active-class="bg-white !text-indigo-600 border-slate-200 shadow-sm"
            >
              Availability Prediction
            </RouterLink>
          <button @click="login" class="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg transition-colors border border-slate-200 shadow-sm flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21v-5h5"/></svg>
            Refresh
          </button>
          <button @click="logout" class="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 text-sm font-medium rounded-lg transition-colors border border-rose-200 shadow-sm">
            Logout
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-8">
        <!-- Reservations Section -->
        <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          <div class="flex items-center gap-2 mb-6">
            <div class="p-2 bg-blue-100 rounded-lg text-blue-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Active Reservations</h2>
          </div>
          
          <div class="overflow-x-auto rounded-xl border border-slate-200">
            <table class="w-full text-sm text-left">
              <thead class="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th scope="col" class="px-6 py-4 font-semibold">Created At</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Expires At</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Spot ID</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Reserved Plate</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-if="reservations.length === 0">
                  <td colspan="5" class="px-6 py-8 text-center text-slate-500">No active reservations.</td>
                </tr>
                <tr v-for="(res, i) in reservations" :key="i" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-4 whitespace-nowrap text-slate-600 font-medium">{{ formatDate(res.created_at) }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-slate-600 font-medium">{{ formatDate(res.expired_at) }}</td>
                  <td class="px-6 py-4 font-semibold text-slate-900">{{ res.spot_id }}</td>
                  <td class="px-6 py-4 text-slate-600 font-mono">{{ res.reserved_plate }}</td>
                  <td class="px-6 py-4">
                    <span class="px-2.5 py-1 text-xs font-semibold rounded-full border uppercase tracking-wide bg-blue-50 text-blue-700 border-blue-200">
                      {{ res.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Anomalies Section -->
        <div class="bg-white border border-slate-200 rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          <div class="flex items-center gap-2 mb-6">
            <div class="p-2 bg-amber-100 rounded-lg text-amber-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Recent Anomalies</h2>
          </div>
          
          <div class="overflow-x-auto rounded-xl border border-slate-200">
            <table class="w-full text-sm text-left">
              <thead class="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th scope="col" class="px-6 py-4 font-semibold">Timestamp</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Spot ID</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Type</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Details</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-if="anomalies.length === 0">
                  <td colspan="4" class="px-6 py-8 text-center text-slate-500">No anomalies detected.</td>
                </tr>
                <tr v-for="(anom, i) in paginatedAnomalies" :key="i" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-4 whitespace-nowrap text-slate-600 font-medium">{{ formatDate(anom.timestamp) }}</td>
                  <td class="px-6 py-4 font-semibold text-slate-900">{{ anom.spot_id || 'N/A' }}</td>
                  <td class="px-6 py-4">
                    <span class="px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full border border-amber-200 uppercase tracking-wide">
                      {{ anom.anomaly_type }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-slate-600 truncate max-w-[250px]" :title="anom.detail">{{ anom.detail }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex items-center justify-between pt-4 mt-2" v-if="anomalies.length > anomaliesPerPage">
            <button 
              @click="prevAnomalyPage" 
              :disabled="anomalyPage === 1"
              class="px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              Previous
            </button>
            <span class="text-sm text-slate-500 font-medium">Page {{ anomalyPage }} of {{ totalAnomalyPages }}</span>
            <button 
              @click="nextAnomalyPage" 
              :disabled="anomalyPage === totalAnomalyPages"
              class="px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              Next
            </button>
          </div>
        </div>

      <div class="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-200/50">
        <ParkingGrid ref="gridRef" :isAdmin="true" @view-logs="handleViewLogs" />
      </div>
        <!-- Logs Section -->
        <div id="logs-section" class="bg-white border border-slate-200 rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2">
              <div class="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
              </div>
              <h2 class="text-xl font-bold text-slate-900">
                Recent Spot Logs <span v-if="selectedSpotId" class="text-indigo-600 ml-2 text-sm font-semibold px-2 py-0.5 bg-indigo-50 rounded-full border border-indigo-100">Spot {{ selectedSpotId }}</span>
              </h2>
            </div>
            <button v-if="selectedSpotId" @click="clearLogFilter" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors border border-slate-200">
              Clear Filter
            </button>
          </div>
          
          <div class="overflow-x-auto rounded-xl border border-slate-200">
            <table class="w-full text-sm text-left">
              <thead class="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th scope="col" class="px-6 py-4 font-semibold">Timestamp</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Spot ID</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Status</th>
                  <th scope="col" class="px-6 py-4 font-semibold">Current Plate</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-if="filteredLogs.length === 0">
                  <td colspan="4" class="px-6 py-8 text-center text-slate-500">
                    <span v-if="selectedSpotId">No logs found for this spot.</span>
                    <span v-else>No recent logs available.</span>
                  </td>
                </tr>
                <tr v-for="(log, i) in paginatedLogs" :key="i" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-4 whitespace-nowrap text-slate-600 font-medium">{{ formatDate(log.timestamp) }}</td>
                  <td class="px-6 py-4 font-semibold text-slate-900">{{ log.spot_id }}</td>
                  <td class="px-6 py-4">
                    <span 
                      class="px-2.5 py-1 text-xs font-semibold rounded-full border uppercase tracking-wide"
                      :class="{
                        'bg-emerald-50 text-emerald-700 border-emerald-200': log.status === 'available',
                        'bg-rose-50 text-rose-700 border-rose-200': log.status === 'occupied',
                        'bg-amber-50 text-amber-700 border-amber-200': log.status === 'reserved',
                        'bg-slate-100 text-slate-700 border-slate-300': !['available', 'occupied', 'reserved'].includes(log.status)
                      }"
                    >
                      {{ log.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-slate-600 font-mono">{{ log.current_plate || '--' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex items-center justify-between pt-4 mt-2" v-if="filteredLogs.length > logsPerPage">
            <button 
              @click="prevLogPage" 
              :disabled="logPage === 1"
              class="px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              Previous
            </button>
            <span class="text-sm text-slate-500 font-medium">Page {{ logPage }} of {{ totalLogPages }}</span>
            <button 
              @click="nextLogPage" 
              :disabled="logPage === totalLogPages"
              class="px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              Next
            </button>
          </div>
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
