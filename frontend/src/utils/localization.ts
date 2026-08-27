/**
 * TasteMap Türkçe Yerelleştirme (Localization) Yardımcıları
 */

export const RESTAURANT_CATEGORIES_TR: Record<string, string> = {
  restaurant: 'Restoran',
  'turkish restaurant': 'Türk Mutfağı',
  'kebab shop': 'Kebapçı',
  'doner kebab restaurant': 'Dönerci',
  'fast food restaurant': 'Fast Food',
  'hamburger restaurant': 'Burger Restoranı',
  'coffee shop': 'Kahve Dükkanı & Kafe',
  cafe: 'Kafe',
  patisserie: 'Pastane & Tatlıcı',
  'dessert restaurant': 'Tatlıcı',
  'chocolate shop': 'Çikolata & Tatlı',
  'dumpling restaurant': 'Mantıcı',
  'sfiha restaurant': 'Pide & Lahmacun',
  'fish restaurant': 'Balık Restoranı',
  'seafood restaurant': 'Deniz Ürünleri',
  'kofta restaurant': 'Köfteci',
  'cig kofte restaurant': 'Çiğ Köfteci',
  'family restaurant': 'Aile Restoranı',
  'pilaf restaurant': 'Pilavcı',
  'catering food and drink supplier': 'Toplu Yemek & Catering',
  'breakfast restaurant': 'Kahvaltıcı',
  'bakery': 'Fırın & Unlu Mamuller',
  'pizzeria': 'Pizzacı',
  'steak house': 'Steakhouse',
  'steakhouse': 'Steakhouse',
  'ice cream shop': 'Dondurmacı',
  'tea house': 'Çay Bahçesi & Kafe',
}

export function formatCategoryTr(category: string | null | undefined): string | null {
  if (!category) return null
  const trimmed = category.trim()
  const lower = trimmed.toLowerCase()
  if (RESTAURANT_CATEGORIES_TR[lower]) {
    return RESTAURANT_CATEGORIES_TR[lower]
  }
  return trimmed
}

export const DAY_NAMES_TR: Record<string, string> = {
  monday: 'Pazartesi',
  tuesday: 'Salı',
  wednesday: 'Çarşamba',
  thursday: 'Perşembe',
  friday: 'Cuma',
  saturday: 'Cumartesi',
  sunday: 'Pazar',
}

export function formatDayNameTr(dayKeyOrLabel: string): string {
  const lower = dayKeyOrLabel.trim().toLowerCase()
  return DAY_NAMES_TR[lower] || dayKeyOrLabel
}

/**
 * 12 saatlik AM/PM saat formatını Türkçe 24 saatlik veya anlaşılır formata çevirir.
 * Örn: "8:30 AM" -> "08:30", "11:30 PM" -> "23:30", "12 AM" -> "00:00", "12 PM" -> "12:00"
 */
function convertAmPmTo24h(timeStr: string): string {
  const match = timeStr.trim().match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$/i)
  if (!match) return timeStr

  let hours = parseInt(match[1], 10)
  const minutes = match[2] ? match[2] : '00'
  const modifier = match[3].toUpperCase()

  if (modifier === 'PM' && hours < 12) {
    hours += 12
  }
  if (modifier === 'AM' && hours === 12) {
    hours = 0
  }

  const hoursFormatted = hours.toString().padStart(2, '0')
  return `${hoursFormatted}:${minutes}`
}

/**
 * Google Maps / SerpAPI'den gelen tekil gün çalışma saatini Türkçeleştirir.
 * Örn: "8:30 AM – 3:30 AM" -> "08:30 – 03:30"
 *      "Open 24 hours" -> "24 Saat Açık"
 *      "Closed" -> "Kapalı"
 */
export function formatDailyHoursTr(hours: string | null | undefined): string {
  if (!hours) return 'Belirtilmedi'
  const trimmed = hours.trim()
  const lower = trimmed.toLowerCase()

  if (lower === 'open 24 hours' || lower === 'open 24 hour') {
    return '24 Saat Açık'
  }
  if (lower === 'closed') {
    return 'Kapalı'
  }

  // Unicode dash, en-dash, em-dash, hyphen normalize
  const normalized = trimmed.replace(/[\u2013\u2014\u2212]/g, '-').replace(/\\u202f/g, ' ').replace(/\\u2013/g, ' - ')

  // Örn: "8:30 AM - 11:30 PM"
  if (normalized.includes('-')) {
    const parts = normalized.split('-').map((p) => p.trim())
    if (parts.length === 2) {
      const start = convertAmPmTo24h(parts[0])
      const end = convertAmPmTo24h(parts[1])
      return `${start} – ${end}`
    }
  }

  return normalized
}

/**
 * Restoran kartı veya detay başlığındaki özet çalışma durumu metnini Türkçeleştirir.
 * Örn:
 * "Open 24 hours" -> "24 Saat Açık"
 * "Open · Closes 11 PM" -> "Açık · Kapanış 23:00"
 * "Open · Closes 11:30 PM" -> "Açık · Kapanış 23:30"
 * "Closed · Opens 9 AM Mon" -> "Kapalı · Açılış Pazartesi 09:00"
 * "Closed · Opens 10:30 AM Mon" -> "Kapalı · Açılış Pazartesi 10:30"
 * "Closes soon · 1 AM · Reopens 10 AM" -> "Kapanmak Üzere · 01:00 · Yeniden Açılış 10:00"
 */
export function formatOpeningHoursTr(hoursText: string | null | undefined): string | null {
  if (!hoursText) return null
  let text = hoursText.trim()
  if (!text) return null

  // Unicode temizliği (özel boşluklar ve tireler)
  text = text.replace(/[\u202F\u00A0]/g, ' ')
  text = text.replace(/[\u2013\u2014\u2212]/g, '-')

  const lower = text.toLowerCase()
  if (lower === 'open 24 hours' || lower === 'open 24 hour') {
    return '24 Saat Açık'
  }
  if (lower === 'closed') {
    return 'Kapalı'
  }
  if (lower === 'open' || lower === 'open now') {
    return 'Şu an Açık'
  }

  let result = text

  // Gün adlarını çevir
  result = result.replace(/\bMon\b/gi, 'Pazartesi')
  result = result.replace(/\bTue\b/gi, 'Salı')
  result = result.replace(/\bWed\b/gi, 'Çarşamba')
  result = result.replace(/\bThu\b/gi, 'Perşembe')
  result = result.replace(/\bFri\b/gi, 'Cuma')
  result = result.replace(/\bSat\b/gi, 'Cumartesi')
  result = result.replace(/\bSun\b/gi, 'Pazar')

  // Ana durum kelimelerini çevir
  result = result.replace(/Closes soon/gi, 'Kapanmak Üzere')
  result = result.replace(/Reopens/gi, 'Açılış')
  result = result.replace(/Opens/gi, 'Açılış')
  result = result.replace(/Closes/gi, 'Kapanış')
  result = result.replace(/\bOpen\b/g, 'Açık')
  result = result.replace(/\bClosed\b/g, 'Kapalı')

  // AM/PM saatlerini 24h formatına dönüştür
  result = result.replace(/(\d{1,2}(?::\d{2})?)\s*(AM|PM)/gi, (match) => convertAmPmTo24h(match))

  return result
}
