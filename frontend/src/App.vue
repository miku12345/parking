<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-700 font-sans selection:bg-indigo-500/20">
    <!-- Navbar -->
    <header class="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-slate-200/80 shadow-sm shadow-slate-200/40">
      <div class="mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16 gap-4">
          <!-- Brand -->
          <RouterLink to="/" class="flex items-center gap-3 group">
            <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 group-hover:bg-indigo-100 transition-colors shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
                <path d="M9 16V8h4a2 2 0 0 1 0 4H9" />
              </svg>
            </div>
            <div>
              <h1 class="text-base font-bold leading-tight text-slate-900 tracking-tight">IOT Smart parking system</h1>
              <p class="text-xs text-slate-500 font-medium tracking-wide">Live Status</p>
            </div>
          </RouterLink>

          <!-- Nav Links -->
          <nav class="flex items-center gap-1 sm:gap-2 bg-slate-100/80 p-1.5 rounded-full border border-slate-200 shadow-inner">
            <RouterLink 
              to="/" 
              class="px-4 py-1.5 rounded-full text-sm font-medium text-slate-500 transition-all hover:text-slate-800 hover:bg-slate-200/50 active-nav-link"
              exact-active-class="bg-white !text-indigo-600 border-slate-200 shadow-sm"
            >
              Dashboard
            </RouterLink>
            <RouterLink 
              to="/admin" 
              class="px-4 py-1.5 rounded-full text-sm font-medium text-slate-500 transition-all hover:text-slate-800 hover:bg-slate-200/50"
              exact-active-class="bg-white !text-indigo-600 border-slate-200 shadow-sm"
            >
              Admin
            </RouterLink>

          </nav>
        </div>
      </div>
    </header>
    <!-- Main Content -->
    <div class="flex justify-center items-center">
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 ">
      
      <RouterView v-slot="{ Component }">
        <transition 
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 -translate-y-4"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
    </div>
  </div>
</template>

<style>
/* Remove old unscoped styles from base.css interfering with new app shell */
body {
  background: transparent !important;
}
</style>
