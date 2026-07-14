# Title: China tax information reporting requirement

Title: China tax information reporting requirement

URL Source: https://sellercentral.amazon.com/help/hub/reference/external/GAHCR5L7VQUNGBJZ

Markdown Content:
Reporting requirements issued by the State Council of China (Decree No. 810) and the State Taxation Administration of China (Public Notice [2025] No. 15) require domestic and foreign online stores to provide information on China-based sellers to the Chinese tax authority.

We’ll provide quarterly reports to the Chinese tax authority that include data such as identity information, number of transactions, revenue, and commission and service fees.

## Who is affected

China-based sellers who sell goods, services, or intangible items to customers in any of Amazon’s worldwide stores.

## Required information

Amazon will report the following information on affected sellers to the Chinese tax authority.

| Data point | Sellers who have obtained a business registration certificate | Sellers who have not obtained a business registration certificate |
| --- | --- | --- |
| Name on the business registration certificate | Yes | No |
| Unified social credit code/taxpayer identification number | Yes | No |
| Name on national ID | No | Yes |
| National ID category and number | No | Yes |
| National ID issuing Country/Region | No | Yes |
| Address | Yes | Yes |
| Online Store Name | Yes | Yes |
| Store URL (Optional) | Yes | Yes |
| Bank Account Details* | Yes | Yes |
| Point of Contact Name | Yes | Yes |
| Contact Phone Number | Yes | Yes |
| Marketplace Company ID (MCID) | Yes | Yes |
| Marketplace | Yes | Yes |
| Total Revenue (CNY) | Yes | Yes |
| Net Income (CNY) | Yes | Yes |
| Refund Amount (CNY) | Yes | Yes |
| Total commission and service fees (CNY) | Yes | Yes |
| Number of transactions (orders) | Yes | Yes |

* Bank account details include bank account or payment account number, account name, and bank or payment institution name.

## Frequently asked questions

#### When was this tax reporting requirement introduced?

In June 2025, the State Council of China issued new reporting requirements under Decree No. 810, and the State Taxation Administration of China released implementation rules through Public Notice [2025] No. 15 (PN15).

#### I'm a China-based seller but I only sell outside of China. Am I affected?

Yes. Reporting requirements apply to all China-based sellers, regardless of which Amazon store you sell in. For example, even if you only sell in the Amazon.com store (United States), your account information and transactions must be reported to the Chinese tax authority.

#### When will the reports be filed?

The first quarterly report covering July to September 2025 was filed on October 31, 2025. We’ll continue to provide quarterly reports on an ongoing basis.

#### Do I need to take any action?

No action is required to comply with this China tax information reporting requirement. We will share the required information with the Chinese tax authorities on a quarterly basis.

To ensure that your data in the report is accurate, make sure that the information in the **Required information** table above is complete and up to date.

**Important:**If your information has already been verified, any changes to your account information will trigger new verification processes in line with regulatory requirements in the stores in which you sell.

#### Will I receive a quarterly statement from Amazon showing what was filed to the Chinese tax authority?

Yes. We will provide you with a copy of the quarterly report shared with the Chinese tax authorities for your reference. We recommend that you maintain a copy of the report for your records.

#### Why do I see differences between data in the quarterly tax report and my reports in Seller Central?

#### Why do I see differences between data in the quarterly tax report and my reports in Seller Central?

Variation between the data in your quarterly report and your payment and Amazon VAT transactions report in the [Reports Repository](https://sellercentral.amazon.com/payments/reports-repository/ref=xx_rrepo_dnav_xx) is expected. Each report uses distinct methodology and serves a different purpose.

The quarterly tax report methodology differs from other reports in the following ways:

The quarterly tax report methodology differs from other reports in the following ways:

*   **Revenue calculation**: We calculate revenue for your worldwide sales based on the [Central Parity Rate](https://www.chinamoney.com.cn/english/bmkcpr/) on the date that your order was shipped to the buyer.
*   **Reporting period**: We report quarterly transactions based on order ship dates.
*   **Definition of revenue**: The calculation includes product sales revenue, shipping fees, gift wrap fees, discounts, taxes, and surcharges.
*   **Fee definition**: The "total amount of commissions and service fees paid to the platform" includes, but is not limited to, referral fees, fulfillment fees, cross-border shipping fees, regulatory advertising fees, and monthly subscription fees.

#### What if my Unified Social Credit Code or Taxpayer Identification Number is not available in my Seller Central account?

#### What if my Unified Social Credit Code or Taxpayer Identification Number is not available in my Seller Central account?

If you don’t have a Unified Social Credit Code or Taxpayer Identification Number in your Seller Central account (for example, if you sell in our Japan or Australia stores), we use your Marketplace Company ID and Marketplace Country Code to complete this field in the report.

#### How do I use the order-level report?

Your revenue report and fee report are grouped in a “.zip” format file. Use dedicated apps for extracting the files. The zip contains a separate file for revenue and fees. Your revenue file or fee file is split into multiple files in case you have more than 1 MM of order-level line data in different stores.

#### What does the order-level report contain?

The order-level report contains a separate folder and file for the reported revenue and fees. It contains granular transactional data of your quarterly report shared.

The files contain the following data points for your reference:

| Data point | Column name | Comments |
| --- | --- | --- |
| Marketplace Name | marketplace_name | Store where the sale took place. |
| Merchant Account Id | account_id | Amazon identifier of the seller account |
| Activity | activity | Type of activity. Order history report includes only transaction types 'SALES' and 'RETURN'. |
| Order Id | order_id | Identification number of the order. |
| Shipment Id | shipment_id | Identification number of the shipment. |
| ASIN | asin | Amazon Standard Identification Number: is a unique product identification number |
| Ship Date | ship_date | Date when the order shipment was dispatched. |
| Fee Date | fee_date | The date, when the commission has been deducted/charged. |
| Fee Description | fee_description | A detailed description of the deducted/charged commission. Amazon doesn’t introduce any new fee via PN15 reporting. The fee description might not be the fee names that you are familiar with, due to translation reasons. |

| Fee Description in Chinese | fee_description_chinese | A detailed description of the deducted/charged commission in Chinese. Amazon doesn’t introduce any new fee via PN15 reporting. The fee description might not be the fee names that you are familiar with, due to translation reasons. |
| Original Currency | original_currency | The three-letter ISO currency code representing the primary/default currency for a transaction (for example, EUR, GBP) |
| Rate | rate | Conversion rate - [Central Parity Rate](https://www.chinamoney.com.cn/english/bmkcpr/) |
| Total in Original Currency | total_in_original_currency | Total price of the order charged to the end customer in original currency. |
| Total in CNY | total_in_cny | Total price of the order charged to the end customer in CNY. |
| Fee Amount in Original Currency | fee_amount_in_original_currency | The NET-paid amount in original currency. |

| Fee Amount in Original Currency | fee_amount_in_original_currency | The NET-paid amount in original currency. |
| Fee Tax Amount in Original Currency | fee_tax_amount_in_original_currency | The TAX amount, which has been calculated for the commission in original currency. |
| Fee Promotion Amount in Original Currency | fee_promotion_amount_in_original_currency | The promotion amount, which got deducted from the commission in original currency. |
| Fee Total in Original Currency | fee_total_in_original_currency | The total commission amount with TAX after deducting promotion in original currency. |
| Fee Amount in CNY | fee_amount_in_cny | Fee Amount in CNY is Fee Amount in Original Currency converted with Rate value. |
| Fee Tax Amount in CNY | fee_tax_amount_in_cny | Fee Tax Amount in CNY is Fee Tax Amount in Original Currency converted with Rate value. |

| Fee Tax Amount in CNY | fee_tax_amount_in_cny | Fee Tax Amount in CNY is Fee Tax Amount in Original Currency converted with Rate value. |
| Fee Promotion Amount in CNY | fee_promotion_amount_in_cny | Fee Promotion Amount in CNY is Fee Promotion Amount in Original Currency converted with Rate value. |
| Fee Total in CNY | fee_total_in_cny | Fee Total in CNY is Fee Total in Original Currency converted with Rate value. |

## What are the fee names included in the Fee Description column of the order-level fee report ?

| Fee Description | Fee Description in Chinese |
| --- | --- |
| Global Inbound Transportation Duty | 入库运输关税 |
| Global Inbound Transportation Freight | 入库运输费 |
| AWD Processing Fee | AWD处理费 |
| AWD Transportation Fee | AWD运输费 |
| AWD MCD Transportation Fee | AWD MCD 运输费 |
| Coupon Participation Fee | 优惠券参与费用 |
| Coupon Performance Based Fee | 优惠券变动费用 |
| Return Processing fee | 退货处理费 |
| Deal Participation Fee | 促销参与费用 |
| Deal Performance Based Fee | 促销变动费用 |
| Disposal Fee | 弃置费 |
| Return Processing fee | 退货处理费 |
| Manual Processing Fee | 手动处理费 |
| FBA Inbound Placement Service Fee | 亚马逊物流入库配置服务费 |
| FBA Inbound Defect Fee | 入库缺陷费 |
| FBA International Freight Shipping Charge | FBA国际货运运费 |
| FBA International Freight Duties and Taxes charge | FBA 国际货运关税和税费 |
| FBA Amazon-Partnered Carrier Shipment Fee | FBA 亚马逊合作承运商运费 |
| Digital Services Fee | 数字服务费 |
| FBA Multi-tier per unit Fee | FBA多件商品每件配送费 |
| Weight Based Fee | 计重收费 |
| High Volume Listing Fee | 大批量上架费用 |

| Digital Services Fee | 数字服务费 |
| FBA Multi-tier per unit Fee | FBA多件商品每件配送费 |
| Weight Based Fee | 计重收费 |
| High Volume Listing Fee | 大批量上架费用 |
| Liquidations processing fee | 清货处理费 |
| Liquidations referral fee | 清货销售佣金 |
| MFN postage fees | MFN运费 |
| Paid Services Fee | 付费服务费用 |
| Referral fee | 销售佣金 |
| Shipping Chargeback | 运费退回 |
| Giftwrap Chargeback | 礼品包装费 |
| Referral fee | 佣金 |
| Digital Services Fee | 数字服务费 |
| Closing fee | 交易手续费 |
| Per-item selling fee | 按件收取的销售费用 |
| Refund administration fee | 退款管理费用 |
| Referral fee | 销售佣金 |
| Invoicing Get Paid Faster Fee | 开票订单更快地获得付款的服务费 |
| Removal fee | 移除费 |
| Deal Fee | Deal 费用 |
| Coupon Fee | 优惠券费用 |
| CSBA Fee | 亚马逊客户服务费 |
| Amazon upstream storage fee | Amazon upstream storage fee |
| Monthly inventory storage fee | 月度仓储费 |
| Aged inventory surcharge | 超龄库存附加费 |
| Subscription Fee | 订阅费 |
| Vine Enrollment Fee | Vine 注册费 |
| Bubble wrap Fee | 气泡膜费 |
| Bagging Fee | 包装费 |
| Labeling Fee | 贴标费 |
| Taping Fee | 贴胶费 |

| Vine Enrollment Fee | Vine 注册费 |
| Bubble wrap Fee | 气泡膜费 |
| Bagging Fee | 包装费 |
| Labeling Fee | 贴标费 |
| Taping Fee | 贴胶费 |
| Customs Duty Fee | 关税费用 |
| EPR Chargeback Service Fee | EPR追缴服务费 |
| EPR Chargeback Eco Fee | EPR追缴环保费 |
| FBA Post Inbound Transportation Program | BA入库后运输计划费用 |
| Order Cancellation Charge | 订单取消费用 |
| ReCommerce Grading And Listing Fee | 二手商品评级与Listing费用 |
| Amazon Accelerator Fee | 亚马逊加速器计划费用 |
| Amazon For All Fee | 亚马逊All计划费用 |
| Amazon Exclusives Fee | 亚马逊独家计划费用 |
| COD Chargeback Fee | 货到付款追缴费用 |
| Sales Tax Collection Fee | 销售税代收费用 |
| Jump Start Your Web store Fee | 大批量上架费 |
| Storage Reservation Fee | 储预留费用 |
| AD-SPONSORED-SELLER | 卖家广告费 |
| imIN | imIN |
| NEMO | NEMO |
| INFO | INFO |

## Where should I check for the PN15 report?

Amazon will send the previous quarter's PN15 submission data to your merchant default email address every quarter. You can view your email address by following steps:

*   Go to [Notification Preferences](https://sellercentral.amazon.com/notifications/preferences).
*   The PN15 report will be sent to the email address displayed in **Merchant Default Contact**.

If you haven't received the email, check whether your mailbox has blocked the email due to security settings.
