# Integracja Enea Wyłączenia dla Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Niestandardowe%20Repozytorium-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Ta integracja dla Home Assistant dostarcza sensory do monitorowania planowanych i nieplanowanych przerw w dostawie prądu od Enea Operator dla określonego regionu i opcjonalnie ulicy.

## Funkcjonalności

*   Monitorowanie liczby planowanych wyłączeń.
*   Monitorowanie liczby nieplanowanych wyłączeń.
*   Dostarczanie podsumowania nadchodzących/obecnych wyłączeń.
*   Sensor binarny wskazujący, czy w danym momencie jakakolwiek przerwa jest aktywna dla skonfigurowanej lokalizacji.
*   Konfigurowalne interwały skanowania dla planowanych i nieplanowanych wyłączeń.
*   Wsparcie dla wielu konfiguracji lokalizacji (regionów/ulic).
*   Tłumaczenia na język angielski i polski.

## Instalacja

Integrację można zainstalować za pomocą HACS (Home Assistant Community Store).

1.  **Dodaj to repozytorium do HACS:**
    *   W Home Assistant przejdź do **HACS** -> **Integracje**.
    *   Kliknij trzy kropki w prawym górnym rogu i wybierz **"Niestandardowe repozytoria"**.
    *   Wprowadź `https://github.com/theundefined/enea-outages-ha/` jako URL repozytorium.
    *   Wybierz `Integracja` jako kategorię.
    *   Kliknij **"Dodaj"**.
2.  **Zainstaluj integrację:**
    *   Wyszukaj "Enea Outages" w HACS i zainstaluj.
3.  **Zrestartuj Home Assistant.**

## Konfiguracja

1.  Po restarcie Home Assistant, przejdź do **Ustawienia** -> **Urządzenia i usługi**.
2.  Kliknij **"DODAJ INTEGRACJĘ"** i wyszukaj "Enea Outages".
3.  Postępuj zgodnie z instrukcjami konfiguracji:
    *   Wybierz swój **Region** z listy rozwijanej (np. "Poznań").
    *   Opcjonalnie, wpisz nazwę **Ulicy**. Jeśli pozostawisz to pole puste, integracja będzie monitorować cały wybrany region.
4.  Po skonfigurowaniu, dla podanej lokalizacji zostanie utworzone nowe urządzenie (np. "Enea Wyłączenia (Poznań, Wojska Polskiego)"). Urządzenie to będzie zawierać:
    *   Sensory z liczbą planowanych i nieplanowanych wyłączeń.
    *   Sensory z podsumowaniem planowanych i nieplanowanych wyłączeń.
    *   Sensor binarny wskazujący, czy jakakolwiek przerwa jest aktywna.

## Usługi

Dostępna jest usługa `enea_outages.update`, która pozwala na ręczne wywołanie aktualizacji wszystkich skonfigurowanych danych Enea Wyłączenia.

## Licencja

Ten projekt jest na licencji Apache 2.0. Zobacz plik [LICENSE](LICENSE), aby uzyskać szczegółowe informacje.

---

*Ten projekt został stworzony z pomocą narzędzi AI (Google Gemini). Mimo że kod został zweryfikowany, prosimy o używanie go ze standardową ostrożnością.*

---
<br>

# Enea Outages Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom%20Repository-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

This Home Assistant integration provides sensors to monitor planned and unplanned power outages from Enea Operator for a specific region and optionally a street.

## Features

*   Monitor count of planned outages.
*   Monitor count of unplanned outages.
*   Provide summary of upcoming/current outages.
*   Binary sensor indicating if any outage is currently active for the configured location.
*   Configurable scan intervals for planned and unplanned outages.
*   Supports multiple locations (regions/streets) configurations.
*   Translated to English and Polish.

## Installation

This integration can be installed via HACS (Home Assistant Community Store).

1.  **Add this repository to HACS:**
    *   In Home Assistant, go to **HACS** -> **Integrations**.
    *   Click the three dots in the top right corner and select **"Custom repositories"**.
    *   Enter `https://github.com/theundefined/enea-outages-ha/` as the Repository URL.
    *   Select `Integration` as the Category.
    *   Click **"Add"**.
2.  **Install the integration:**
    *   Search for "Enea Outages" in HACS and install it.
3.  **Restart Home Assistant.**

## Configuration

1.  After restarting Home Assistant, go to **Settings** -> **Devices & Services**.
2.  Click **"ADD INTEGRATION"** and search for "Enea Outages".
3.  Follow the configuration flow:
    *   Select your **Region** from the dropdown list (e.g., "Poznań").
    *   Optionally, enter a **Street** name. If left empty, the integration will monitor the entire selected region.
4.  Once configured, a new device will be created for your specified location (e.g., "Enea Outages (Poznań, Wojska Polskiego)"). This device will contain:
    *   Sensors for planned and unplanned outage counts.
    *   Sensors for planned and unplanned outage summaries.
    *   A binary sensor indicating if any outage is active.

## Services

A service `enea_outages.update` is available to manually trigger an update of all configured Enea Outages data.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---

*This project was developed with the assistance of AI tools (Google Gemini). While the code has been reviewed, please use it with standard caution.*
