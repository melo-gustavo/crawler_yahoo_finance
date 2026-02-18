import csv
import io
import logging
import time
from typing import Any

from bs4 import BeautifulSoup
from fastapi import HTTPException, Request, Response
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawlers.base_crawler import BaseCrawler
from schemas.crawler import FinancialDataResult, FinancialRow
from utils.contants import (
    PAGINATION_BETWEEN_PAGES_SECONDS,
    PAGINATION_CLICK_SETTLE_SECONDS,
    PAGINATION_CHANGE_TIMEOUT_SECONDS,
    PAGINATION_MAX_ATTEMPTS,
    PAGINATION_POLL_INTERVAL_SECONDS,
    WAIT_SECONDS,
    EQUITY_SCREENER_URL,
)

logger = logging.getLogger(__name__)

CLICK_SCRIPT_ARGUMENT = "arguments[0].click();"
TABLE_ROW_SELECTOR = "//table//tbody//tr"
SCROLL_ARGUMENT = "arguments[0].scrollIntoView({block: 'center'});"


class FinancialYahoo:
    def get_attrs(
        self,
        request: Request,
        region: str,
        max_pages: int | None = None,
        headless: bool = False,
    ) -> FinancialDataResult:
        crawler = BaseCrawler()
        normalized_region = region.title()

        if max_pages is not None and max_pages < 1:
            raise HTTPException(
                status_code=400, detail="max_pages must be greater than or equal to 1."
            )

        driver: WebDriver | None = None
        browser = "Unknown"

        try:
            driver, browser = crawler._start_session(request, headless=headless)
            logger.info(
                "Starting Yahoo crawler for region=%s using browser=%s",
                normalized_region,
                browser,
            )

            driver.get(EQUITY_SCREENER_URL)

            logger.info("Waiting for page to load...")
            crawler._wait_page_load(driver)

            logger.info("Updating region filter...")
            self._search_and_change_filter(driver, normalized_region)

            logger.info("Collecting table data...")
            data = self._select_max_rows_and_get_all_data(
                driver,
                normalized_region,
                max_pages=max_pages,
            )
            if not data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No records found for region '{normalized_region}'.",
                )

            return FinancialDataResult(
                browser=browser,
                region=normalized_region,
                max_pages=max_pages,
                headless=headless,
                total_records=len(data),
                data=data,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            crawler._finish_session(driver)

    def _closing_all_tooltips(self, driver: WebDriver) -> None:
        done_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Done')]")
        for i, done_btn in enumerate(done_buttons):
            try:
                driver.execute_script(CLICK_SCRIPT_ARGUMENT, done_btn)
                logger.info(f"'Done' button #{i + 1} clicked")
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Error clicking 'Done' button #{i + 1}: {str(e)}")

        time.sleep(0.5)

    def _click_region_filter(self, driver: WebDriver) -> None:
        try:
            button = driver.find_element(By.XPATH, "//button[contains(., 'Region')]")
            driver.execute_script(CLICK_SCRIPT_ARGUMENT, button)
            logger.info("Region button clicked successfully")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error clicking Region button: {str(e)}")
            raise

    def _uncheck_current_region(self, driver: WebDriver) -> None:
        try:
            selected_region = self._get_selected_region(driver)
            if not selected_region:
                logger.info("No region currently selected, skipping uncheck step")
                return

            logger.info(
                f"Currently selected region: '{selected_region}' - attempting to uncheck"
            )
            all_labels = driver.find_elements(By.XPATH, "//label")
            for label in all_labels:
                if not label.is_displayed():
                    continue
                label_text = " ".join(label.text.split()).strip().lower()
                if label_text == selected_region.strip().lower():
                    driver.execute_script(CLICK_SCRIPT_ARGUMENT, label)
                    logger.info(f"Region '{selected_region}' unchecked successfully")
                    time.sleep(0.5)
                    return

            logger.warning(
                f"Could not find checkbox for currently selected region '{selected_region}' to uncheck"
            )

        except Exception as e:
            logger.warning(f"Error during unchecking current region: {str(e)}")

    def _get_region_search_input_selectors(self) -> list[str]:
        return [
            "//input[@placeholder='Search regions']",
            "//input[@placeholder='Search...']",
            "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'search')]",
            "//div[@role='dialog' or contains(@class,'dialog') or contains(@class,'menu') or contains(@class,'dropdown')]//input",
        ]

    def _find_region_search_input(self, driver: WebDriver) -> Any:
        for selector in self._get_region_search_input_selectors():
            try:
                candidates = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(
                    f"Error searching region input with selector '{selector}': {str(e)}"
                )
                continue

            for candidate in candidates:
                if candidate.is_displayed() and candidate.is_enabled():
                    return candidate

        return None

    def _fill_region_search_input(self, driver: WebDriver, search_input: Any, region: str) -> bool:
        try:
            WebDriverWait(driver, WAIT_SECONDS).until(
                EC.element_to_be_clickable(search_input)
            )
            driver.execute_script(SCROLL_ARGUMENT, search_input)
            time.sleep(0.2)
            search_input.click()
            search_input.clear()
            search_input.send_keys(region)
            logger.info(f"Region '{region}' entered in search input")
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.warning(
                f"Standard input interaction failed, trying JS fallback: {str(e)}"
            )
            return False

    def _fill_region_search_input_fallback(
        self, driver: WebDriver, search_input: Any, region: str
    ) -> None:
        try:
            driver.execute_script(
                """
                const input = arguments[0];
                const value = arguments[1];
                input.focus();
                input.value = '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.value = value;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                search_input,
                region,
            )
            logger.info(f"Region '{region}' entered in search input via JS fallback")
            time.sleep(0.5)
        except Exception as fallback_error:
            logger.warning(
                f"Error entering region in search input: {str(fallback_error)}"
            )

    def _filtering_region_by_search(self, driver: WebDriver, region: str) -> None:
        search_input = self._find_region_search_input(driver)
        if not search_input:
            logger.warning("Search input not found or not interactive")
            return

        filled = self._fill_region_search_input(driver, search_input, region)
        if not filled:
            self._fill_region_search_input_fallback(driver, search_input, region)

    def _select_region_from_results(self, driver: WebDriver, region: str) -> None:
        all_labels = driver.find_elements(By.XPATH, "//label")
        normalized_region = region.strip().lower()
        exact_matches = []
        partial_matches = []
        for label in all_labels:
            if not label.is_displayed():
                continue
            label_text = " ".join(label.text.split()).strip().lower()
            if not label_text:
                continue
            if label_text == normalized_region:
                exact_matches.append(label)
            elif normalized_region in label_text:
                partial_matches.append(label)

        label_select = (exact_matches or partial_matches or [None])[0]
        if label_select is None:
            raise ValueError(f"Region '{region}' is invalid or not available.")

        driver.execute_script(CLICK_SCRIPT_ARGUMENT, label_select)
        logger.info(f"Region '{region}' selected successfully")
        time.sleep(0.5)

    def _waiting_and_clicking_apply(self, driver: WebDriver, region: str) -> None:
        try:
            apply_button = WebDriverWait(driver, WAIT_SECONDS).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Apply')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
            time.sleep(0.3)
            driver.execute_script(CLICK_SCRIPT_ARGUMENT, apply_button)
            logger.info("'Apply' button clicked successfully")
        except Exception as e:
            logger.warning(f"Error clicking 'Apply' button: {str(e)}")

        time.sleep(0.5)
        filter_applied = self._wait_for_filtered_data(driver, region)
        if not filter_applied:
            raise ValueError(f"Region '{region}' could not be applied.")

    def _search_and_change_filter(self, driver: WebDriver, region: str) -> None:
        """Apply the region filter using the screener UI flow:

        1. Click all "Done" buttons to close tooltips
        2. Open the Region filter
        3. Uncheck the currently selected region
        4. Search for the target region in the input
        5. Select the target region and click Apply
        """
        try:
            logger.info("Step 1: Closing all 'Done' tooltip buttons")
            self._closing_all_tooltips(driver)

            logger.info("Step 2: Clicking the Region button")
            self._click_region_filter(driver)

            logger.info("Step 3: Unchecking currently selected region")
            self._uncheck_current_region(driver)

            logger.info(f"Step 4: Filtering by '{region}' in the Region select input")
            self._filtering_region_by_search(driver, region)

            logger.info(f"Step 5: Selecting region '{region}'")
            self._select_region_from_results(driver, region)

            logger.info("Waiting and clicking 'Apply'")
            self._waiting_and_clicking_apply(driver, region)

        except Exception as e:
            logger.error(f"Error selecting region: {str(e)}")
            raise

    def _wait_for_filtered_data(self, driver: WebDriver, expected_region: str) -> bool:
        """Wait for the table to reload after applying the region filter."""
        try:
            logger.info(f"Waiting for data to load for region '{expected_region}'")

            WebDriverWait(driver, WAIT_SECONDS).until(
                EC.presence_of_all_elements_located((By.XPATH, TABLE_ROW_SELECTOR))
            )
            logger.info("Table loaded")

            time.sleep(0.3)

            current_region = self._get_selected_region(driver)
            if current_region and expected_region.lower() in current_region.lower():
                logger.info(
                    f"Filter confirmed: region '{current_region}' selected correctly"
                )
                return True
            else:
                logger.warning(
                    f"Selected region: '{current_region}', expected: '{expected_region}'"
                )
                return False

        except TimeoutException:
            logger.error(
                f"Timeout while waiting for data to load for region '{expected_region}'"
            )
            return False
        except Exception as e:
            logger.error(f"Error while waiting for filtered data: {str(e)}")
            return False

    def _get_selected_region(self, driver: WebDriver) -> str | None:
        """Return the currently selected value from the Region filter."""
        try:
            val_element = driver.find_element(
                By.XPATH,
                "//button[contains(., 'Region')]//div[@class='val'] | //button[contains(., 'Region')]//div[contains(@class, 'val')]",
            )
            selected_region = val_element.text.strip()
            logger.info(f"Selected region found: {selected_region}")
            return selected_region
        except Exception as e:
            logger.warning(f"Error extracting selected region: {str(e)}")
            return None

    def _select_max_rows_and_get_all_data(
        self,
        driver: WebDriver,
        region: str,
        max_pages: int | None = None,
    ) -> list[FinancialRow]:
        """Wait until the table is ready and extract all visible rows."""
        try:
            logger.info("Waiting for table to be ready before selecting rows per page")
            WebDriverWait(driver, WAIT_SECONDS).until(
                EC.presence_of_all_elements_located((By.XPATH, TABLE_ROW_SELECTOR))
            )

            self._set_max_rows_per_page(driver)
            time.sleep(0.5)

            data = self._paginate_and_collect_data(driver, max_pages=max_pages)
            logger.info(
                f"Extracted data for region '{region}': {len(data)} records found"
            )
            return data

        except Exception as e:
            logger.error(f"Error selecting maximum rows per page: {str(e)}")
            return []

    def _get_enabled_next_button(self, driver: WebDriver) -> Any:
        try:
            next_candidates = []
            exact_selectors = [
                (By.CSS_SELECTOR, "button[data-testid='next-page-button']"),
                (By.XPATH, "//button[@aria-label='Goto next page']"),
                (
                    By.XPATH,
                    "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next page')]",
                ),
            ]

            for by, selector in exact_selectors:
                found = driver.find_elements(by, selector)
                if found:
                    next_candidates.extend(found)

            if not next_candidates:
                next_candidates = driver.find_elements(
                    By.XPATH,
                    "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next') "
                    "or contains(translate(@title,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next') "
                    "or contains(translate(@data-test,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next') "
                    "or contains(translate(@data-testid,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next')]",
                )

            for btn in next_candidates:
                disabled_attr = (btn.get_attribute("disabled") or "").lower()
                aria_disabled = (btn.get_attribute("aria-disabled") or "").lower()
                class_name = (btn.get_attribute("class") or "").lower()
                is_disabled = (
                    disabled_attr in {"true", "disabled"}
                    or aria_disabled == "true"
                    or "disabled" in class_name
                    or not btn.is_enabled()
                )
                if btn.is_displayed() and not is_disabled:
                    return btn
        except Exception as e:
            logger.debug(f"Error searching next button: {e}")

        return None

    def get_first_row_snapshot(self, driver: WebDriver) -> str:
        rows = driver.find_elements(By.XPATH, TABLE_ROW_SELECTOR)
        if not rows:
            return ""
        return " ".join(rows[0].text.split())

    def wait_for_table_change(
        self, driver: WebDriver, previous_snapshot: str, timeout_seconds: float
    ) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            rows = driver.find_elements(By.XPATH, TABLE_ROW_SELECTOR)
            if rows:
                current_snapshot = " ".join(rows[0].text.split())
                if current_snapshot and current_snapshot != previous_snapshot:
                    return True
            time.sleep(PAGINATION_POLL_INTERVAL_SECONDS)
        return False

    def _build_page_signature(self, page_data: list[FinancialRow]) -> tuple[str, ...]:
        return tuple(item.symbol for item in page_data[:5])

    def _get_current_table_signature(self, driver: WebDriver) -> tuple[str, ...]:
        return tuple(
            el.text.strip()
            for el in driver.find_elements(By.XPATH, "//table//tbody//tr/td[1]")[:5]
        )

    def _click_next_and_detect_change(
        self,
        driver: WebDriver,
        next_button: Any,
        previous_signature: tuple[str, ...],
    ) -> bool:
        previous_snapshot = self.get_first_row_snapshot(driver)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'nearest'});", next_button
        )
        time.sleep(0.3)
        driver.execute_script(CLICK_SCRIPT_ARGUMENT, next_button)
        time.sleep(PAGINATION_CLICK_SETTLE_SECONDS)

        changed_by_snapshot = self.wait_for_table_change(
            driver,
            previous_snapshot,
            timeout_seconds=PAGINATION_CHANGE_TIMEOUT_SECONDS,
        )
        changed_by_signature = (
            self._get_current_table_signature(driver) != previous_signature
        )
        return changed_by_snapshot or changed_by_signature

    def _advance_to_next_page(
        self,
        driver: WebDriver,
        page_num: int,
        signature: tuple[str, ...],
        next_button: Any,
    ) -> bool:
        for attempt in range(1, PAGINATION_MAX_ATTEMPTS + 1):
            logger.info(
                f"Paginating to page {page_num + 1}, attempt {attempt}/{PAGINATION_MAX_ATTEMPTS}"
            )

            if self._click_next_and_detect_change(driver, next_button, signature):
                logger.info("Page loaded successfully")
                return True

            logger.warning("Timeout while waiting for table change after clicking Next")
            next_button = self._get_enabled_next_button(driver)
            if not next_button:
                logger.info("Last page confirmed: Next button unavailable")
                return False

        return False

    def _paginate_and_collect_data(
        self,
        driver: WebDriver,
        max_pages: int | None = None,
    ) -> list[FinancialRow]:
        """Iterate through all pages with 100 rows per page and collect all data."""
        all_data: list[FinancialRow] = []
        page_num = 1
        seen_signatures: set[tuple[str, ...]] = set()

        try:
            while True:
                logger.info(f"Collecting data from page {page_num}")

                page_data = self._extract_table_data(driver)
                logger.info(f"Page {page_num}: {len(page_data)} records extracted")
                if not page_data:
                    logger.info("No data on current page, finishing pagination")
                    break

                signature = self._build_page_signature(page_data)
                if signature in seen_signatures:
                    logger.info("Repeated page detected, finishing pagination")
                    break

                seen_signatures.add(signature)
                all_data.extend(page_data)

                if max_pages is not None and page_num >= max_pages:
                    logger.info(f"Page limit reached: {max_pages}")
                    break

                next_button = self._get_enabled_next_button(driver)
                if not next_button:
                    logger.info("End of pagination: next page button unavailable")
                    break

                changed_page = self._advance_to_next_page(
                    driver, page_num, signature, next_button
                )
                if not changed_page:
                    logger.info(
                        "Could not advance page after retries, ending pagination"
                    )
                    break

                time.sleep(PAGINATION_BETWEEN_PAGES_SECONDS)
                page_num += 1

        except Exception as e:
            logger.error(f"Error during pagination: {str(e)}")

        logger.info(
            f"Total records collected: {len(all_data)} across {page_num} page(s)"
        )
        return all_data

    def _find_rows_per_page_dropdown(self, driver: WebDriver) -> Any:
        selectors_priority = [
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'rows')]",
            "//*[contains(@class,'dropdown')]//button",
        ]

        for selector in selectors_priority:
            try:
                dropdowns = driver.find_elements(By.XPATH, selector)
            except Exception as e:
                logger.debug(f"Selector did not match: {e}")
                continue

            for dropdown in dropdowns:
                if dropdown.is_displayed() and dropdown.size["height"] > 0:
                    logger.info(f"Dropdown found: {dropdown.text.strip()}")
                    return dropdown

        return None

    def _wait_for_rows_option_dialog(self, driver: WebDriver) -> None:
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//div[@role='dialog' or contains(@class,'dialog') or contains(@class,'menu') or contains(@class,'dropdown')]"
                        "//*[(@role='option' or @data-value='100' or self::button) and contains(normalize-space(.), '100')]",
                    )
                )
            )
            logger.info("Dropdown options detected")
        except TimeoutException:
            logger.warning("Timeout while waiting for dropdown options")
            logger.info("Trying to continue anyway")

    def _try_select_100_option(self, driver: WebDriver) -> bool:
        option_selectors = [
            "//div[@role='dialog' or contains(@class,'dialog') or contains(@class,'menu') or contains(@class,'dropdown')]//*[@data-value='100']",
            "//div[@role='dialog' or contains(@class,'dialog') or contains(@class,'menu') or contains(@class,'dropdown')]//*[@role='option' and contains(normalize-space(.), '100')]",
            "//button[contains(normalize-space(.), '100')]",
        ]

        for selector in option_selectors:
            try:
                candidates = driver.find_elements(By.XPATH, selector)
            except Exception as e:
                logger.debug(f"Failure in option-100 selector: {e}")
                continue

            for candidate in candidates:
                if not candidate.is_displayed():
                    continue
                driver.execute_script(SCROLL_ARGUMENT, candidate)
                time.sleep(0.1)
                driver.execute_script(CLICK_SCRIPT_ARGUMENT, candidate)
                logger.info("Option 100 clicked successfully")
                return True

        return False

    def _fallback_select_100_option(self, driver: WebDriver) -> str:
        return driver.execute_script("""
            const allElements = Array.from(document.querySelectorAll('*'));
            const candidates = allElements.filter(el => {
                const text = (el.textContent || '').trim();
                const rect = el.getBoundingClientRect();
                const role = (el.getAttribute('role') || '').toLowerCase();
                const dataValue = el.getAttribute('data-value');
                const clickable = role === 'option' || el.tagName === 'BUTTON' || dataValue === '100';
                return rect.height > 0 && rect.width > 0 && clickable && (text === '100' || dataValue === '100');
            });
            if (candidates.length > 0) {
                candidates[0].scrollIntoView({block: 'center'});
                candidates[0].click();
                return 'Opção 100 clicada via fallback JS';
            }
            return 'Opção 100 não encontrada';
        """)

    def _get_visible_table_rows_count(self, driver: WebDriver) -> int:
        return driver.execute_script("""
            const rows = document.querySelectorAll('table tbody tr');
            return rows.length;
        """)

    def _set_max_rows_per_page(self, driver: WebDriver) -> None:
        """Set 'Rows per page' to 100 using a more reliable selection method."""
        logger.info("Starting _set_max_rows_per_page")

        try:
            logger.info("Step 1: Finding 'Rows per page' dropdown")
            dropdown = self._find_rows_per_page_dropdown(driver)
            if not dropdown:
                logger.warning("Dropdown not found - aborting")
                return

            logger.info("Step 2: Opening dropdown")
            driver.execute_script(SCROLL_ARGUMENT, dropdown)
            time.sleep(0.2)
            driver.execute_script(CLICK_SCRIPT_ARGUMENT, dropdown)
            logger.info("Dropdown clicked")
            time.sleep(0.8)

            logger.info("Step 3: Waiting for dropdown options to become visible")
            self._wait_for_rows_option_dialog(driver)

            time.sleep(0.2)

            logger.info("Step 4: Finding and selecting option '100'")
            selected = self._try_select_100_option(driver)

            if not selected:
                result = self._fallback_select_100_option(driver)
                logger.info(f"Fallback selection result: {result}")
            time.sleep(0.5)

            logger.info("Step 5: Verifying if 100 was selected")
            rows_count = self._get_visible_table_rows_count(driver)
            logger.info(f"Confirmation: table has {rows_count} visible rows")

        except Exception as e:
            logger.error(f"General error in _set_max_rows_per_page: {str(e)}")

        logger.info("End _set_max_rows_per_page")

    def _extract_table_data(self, driver: WebDriver) -> list[FinancialRow]:
        """Extract table rows as symbol, name, and price dictionaries."""
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.select_one("table")
            if table is None:
                logger.warning("No table found in page source.")
                return []

            header_cells = table.select("thead th")
            headers = [cell.get_text(" ", strip=True).lower() for cell in header_cells]

            def find_index(possible_names: list[str], default: int) -> int:
                for i, header in enumerate(headers):
                    if any(name in header for name in possible_names):
                        return i
                return default

            symbol_index = find_index(["symbol", "ticker"], 0)
            name_index = find_index(["name", "company"], 1)
            price_index = find_index(["price", "last price"], 2)

            rows = table.select("tbody tr")
            data: list[FinancialRow] = []
            for row in rows:
                cells = row.select("td")
                max_required_index = max(symbol_index, name_index, price_index)
                if len(cells) <= max_required_index:
                    continue

                symbol_raw = cells[symbol_index].get_text("\n", strip=True)
                symbol = symbol_raw.split("\n")[-1].strip()
                company_name = cells[name_index].get_text(" ", strip=True)
                price_value = cells[price_index].get_text(" ", strip=True)

                record = FinancialRow(
                    symbol=symbol,
                    name=company_name,
                    price=price_value,
                )
                data.append(record)
            return data
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}")
            return []

    def generate_csv(
        self,
        request: Request,
        region: str,
        max_pages: int | None = None,
        headless: bool = False,
    ) -> Response | Any:
        result = self.get_attrs(
            request=request,
            region=region,
            max_pages=max_pages,
            headless=headless,
        )
        rows = result.data
        normalized_region = str(result.region or region).lower()
        logger.info(
            "CSV rows to export for region=%s: %s", normalized_region, len(rows)
        )

        output = io.StringIO(newline="")
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(["symbol", "name", "price"])

        for row in rows:
            writer.writerow(
                [
                    str(row.symbol),
                    str(row.name),
                    str(row.price),
                ]
            )

        csv_content = output.getvalue()
        csv_content_with_bom = csv_content.encode("utf-8-sig")
        return Response(
            content=csv_content_with_bom,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="financial_{normalized_region}.csv"'
            },
        )
