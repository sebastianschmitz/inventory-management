<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.subtitle') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          step="1000"
          :style="{ '--fill': fillPercent + '%' }"
          :aria-label="t('restocking.budgetLabel')"
          :disabled="candidates.length === 0"
        />
        <div class="slider-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.recommendedSpend') }}</div>
          <div class="stat-value">{{ money(recommendedSpend) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.items') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="showConfirm = true"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ candidates.length === 0 ? t('restocking.noCandidates') : t('restocking.empty') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>{{ rec.supplier }}</td>
                <td class="num">{{ rec.quantity }}</td>
                <td class="num">{{ money(rec.unitCost, true) }}</td>
                <td class="num"><strong>{{ money(rec.lineTotal) }}</strong></td>
                <td class="num">{{ rec.leadTime }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showConfirm" class="modal-overlay" @click="closeConfirm">
          <div class="modal-container" @click.stop>
            <div class="modal-header">
              <h3 class="modal-title">{{ t('restocking.confirmTitle') }}</h3>
            </div>
            <div class="modal-body">
              <p class="confirm-text">{{ t('restocking.confirmMessage', { count: recommendations.length }) }}</p>
              <div class="confirm-row">
                <span>{{ t('restocking.confirmTotal') }}</span>
                <strong>{{ money(recommendedSpend) }}</strong>
              </div>
              <div class="confirm-row">
                <span>{{ t('restocking.confirmLeadTime') }}</span>
                <strong>{{ t('restocking.days', { count: longestLeadTime }) }}</strong>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-secondary" :disabled="submitting" @click="closeConfirm">
                {{ t('restocking.cancel') }}
              </button>
              <button class="btn-primary" :disabled="submitting" @click="placeOrder">
                {{ submitting ? t('restocking.placing') : t('restocking.confirm') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const STEP = 1000

export default {
  name: 'Restocking',
  setup() {
    // NOTE: The global FilterBar (period/warehouse/category/status) is intentionally
    // ignored on this tab: restocking plans against total stock across all warehouses.
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventory = ref([])
    const budget = ref(0) // always held in USD
    const budgetInitialized = ref(false)
    const showConfirm = ref(false)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    // Amounts are stored in USD; convert for display only
    const money = (amount, decimals = false) => {
      return decimals
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, 2)
        : formatCurrency(amount, currentCurrency.value)
    }

    // Total on-hand per SKU across all warehouses
    const onHandBySku = computed(() => {
      const map = {}
      for (const item of inventory.value) {
        map[item.sku] = (map[item.sku] || 0) + (Number(item.quantity_on_hand) || 0)
      }
      return map
    })

    // Items with non-decreasing demand whose forecast exceeds stock; order the shortfall
    const candidates = computed(() => {
      return forecasts.value
        .filter(f => f.trend !== 'decreasing')
        .map(f => {
          const need = f.forecasted_demand - (onHandBySku.value[f.item_sku] || 0)
          return {
            sku: f.item_sku,
            name: f.item_name,
            supplier: f.supplier,
            trend: f.trend,
            growth: f.forecasted_demand - f.current_demand,
            quantity: need,
            unitCost: f.unit_cost,
            lineTotal: need * f.unit_cost,
            leadTime: f.lead_time_days
          }
        })
        .filter(c => c.quantity > 0)
    })

    // Slider max: total candidate cost rounded up to the next step
    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.lineTotal, 0)
      return Math.ceil(total / STEP) * STEP
    })

    const fillPercent = computed(() => {
      return maxBudget.value > 0 ? Math.min(100, (budget.value / maxBudget.value) * 100) : 0
    })

    // Rank: increasing before stable, then by growth; greedily take whole items that fit
    const recommendations = computed(() => {
      const rank = { increasing: 0, stable: 1 }
      const ranked = [...candidates.value].sort((a, b) => {
        return (rank[a.trend] - rank[b.trend]) || (b.growth - a.growth)
      })
      let left = budget.value
      const picked = []
      for (const c of ranked) {
        if (c.lineTotal <= left) {
          picked.push(c)
          left -= c.lineTotal
        }
        // otherwise skip and keep trying cheaper items further down the ranking
      }
      return picked
    })

    const recommendedSpend = computed(() => recommendations.value.reduce((s, r) => s + r.lineTotal, 0))
    const remaining = computed(() => Math.max(0, budget.value - recommendedSpend.value))
    const longestLeadTime = computed(() => Math.max(0, ...recommendations.value.map(r => r.leadTime || 0)))

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastData
        inventory.value = inventoryData

        if (!budgetInitialized.value) {
          // Default to roughly half of max, snapped to the slider step
          budget.value = Math.round(maxBudget.value / 2 / STEP) * STEP
          budgetInitialized.value = true
        } else {
          budget.value = Math.min(budget.value, maxBudget.value)
        }
      } catch (err) {
        error.value = t('restocking.loadError') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    const closeConfirm = () => {
      if (!submitting.value) showConfirm.value = false
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return
      submitting.value = true
      submitError.value = null
      successMessage.value = null
      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
        showConfirm.value = false
        successMessage.value = t('restocking.successMessage', {
          orderNumber: order.order_number,
          days: order.lead_time_days
        })
        await loadData()
      } catch (err) {
        showConfirm.value = false
        submitError.value = err.response?.data?.detail || t('restocking.errorMessage')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      translateProductName,
      loading,
      error,
      budget,
      maxBudget,
      fillPercent,
      candidates,
      recommendations,
      recommendedSpend,
      remaining,
      longestLeadTime,
      showConfirm,
      submitting,
      submitError,
      successMessage,
      money,
      closeConfirm,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

/* Custom range slider: filled blue track up to the thumb */
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  background: linear-gradient(to right, #2563eb var(--fill), #e2e8f0 var(--fill));
}

.budget-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.35);
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.35);
}

.budget-slider:focus-visible {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.num {
  text-align: right;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.success-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 0 0 1.25rem;
  font-size: 0.938rem;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Confirmation modal (same pattern as BacklogDetailModal) */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 460px;
  width: 100%;
  overflow: hidden;
}

.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.modal-body {
  padding: 1.5rem;
}

.confirm-text {
  color: #475569;
  font-size: 0.938rem;
  margin-bottom: 1rem;
}

.confirm-row {
  display: flex;
  justify-content: space-between;
  padding: 0.625rem 0;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.938rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
