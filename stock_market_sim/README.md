# API Documentation

## Base Path: `/`

### API Endpoints

#### 1. Initialize Server
**Endpoint:** `/init-server`  
**Method:** `GET`  
**Description:** Initialize a new exchange server.  
**Responses:**
- **200 (Success)**
  - Schema: `InitResponse`
  - Description: Returns the exchange ID and a message.

---

#### 2. Add News
**Endpoint:** `/{exchange_id}/add-news`  
**Method:** `POST`  
**Description:** Add news affecting the stock market.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `NewsBody`
- **Responses:**
  - **200 (Success)**
    - Schema: `NewsResponse`
    - Description: News successfully added.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 3. Connect User
**Endpoint:** `/{exchange_id}/connect`  
**Method:** `POST`  
**Description:** Connect a user to the exchange.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `ConnectBody`
- **Responses:**
  - **200 (Success)**
    - Schema: `ConnectResponse`
    - Description: User successfully connected.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 4. Get Users
**Endpoint:** `/{exchange_id}/get-users`  
**Method:** `GET`  
**Description:** Get the list of users connected to the exchange.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `GetUsersResponse`
    - Description: Returns the list of users.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 5. User Inbox
**Endpoint:** `/{exchange_id}/inbox/{user_id}`  
**Method:** `GET`  
**Description:** Get the list of pending trade requests for a user.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
  - `user_id` (string): User ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `InboxResponse`
    - Description: Returns the user's inbox.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 6. Market Data
**Endpoint:** `/{exchange_id}/market-data`  
**Method:** `GET`  
**Description:** Get the current market data.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `MarketDataResponse`
    - Description: Returns market data.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 7. Place Order
**Endpoint:** `/{exchange_id}/order`  
**Method:** `POST`  
**Description:** Place a buy or sell order.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `Order`
- **Responses:**
  - **200 (Success)**
    - Schema: `OrderResponse`
    - Description: Order successfully placed.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 8. Pause Market
**Endpoint:** `/{exchange_id}/pause`  
**Method:** `GET`  
**Description:** Pause the market simulation.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `PauseResponse`
    - Description: Market simulation paused.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 9. Resume Market
**Endpoint:** `/{exchange_id}/resume`  
**Method:** `GET`  
**Description:** Resume the market simulation.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `ResumeResponse`
    - Description: Market simulation resumed.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 10. Start Server
**Endpoint:** `/{exchange_id}/start-server`  
**Method:** `POST`  
**Description:** Start the server with the given configuration.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `ConfigBody`
- **Responses:**
  - **200 (Success)**
    - Schema: `StartResponse`
    - Description: Server started with given configuration.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 11. Stop Server
**Endpoint:** `/{exchange_id}/stop`  
**Method:** `GET`  
**Description:** Stop the market simulation.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Responses:**
  - **200 (Success)**
    - Schema: `StopResponse`
    - Description: Market simulation stopped.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 12. Trade Request
**Endpoint:** `/{exchange_id}/trade-request`  
**Method:** `POST`  
**Description:** Send a trade request to another user.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `TradeRequest`
- **Responses:**
  - **200 (Success)**
    - Schema: `TradeRequestResponse`
    - Description: Trade request successfully sent.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

#### 13. Trade Response
**Endpoint:** `/{exchange_id}/trade-response`  
**Method:** `POST`  
**Description:** Respond to a trade request.  
**Parameters:**
- **Path Parameters:**
  - `exchange_id` (string): Exchange ID.
- **Body Parameters:**
  - Schema: `TradeResponse`
- **Responses:**
  - **200 (Success)**
    - Schema: `TradeResponseResponse`
    - Description: Trade response successfully sent.
  - **400 (Validation Error)**
    - Schema: `ErrorResponse`
    - Description: Validation error message.

---

### Definitions

#### InitResponse
- **exchange_id** (string): Unique identifier for the exchange.
- **message** (string): Description of the action taken.

#### ConfigBody
- **difficulty** (integer): Difficulty level of the simulation (1 to 5 inclusive).
- **stocks** (array of strings): List of stocks to include in the simulation.

#### StartResponse
- **message** (string): Description of the error.

#### ErrorResponse
- **message** (string): Error message.

#### MarketDataResponse
- **details** (object): Account details of all users.
- **prices** (object): Current prices of stocks.

#### NewsBody
- **stock** (string): Stock to affect.
- **impact** (string): Sentiment of the news headline (up or down).

#### NewsResponse
- **message** (string): Description of the action taken.

#### PauseResponse
- **message** (string): Description of the action taken.

#### ResumeResponse
- **message** (string): Description of the action taken.

#### StopResponse
- **message** (string): Description of the action taken.

#### ConnectBody
- **name** (string): Name of the user connecting to the exchange.

#### ConnectResponse
- **message** (string): Description of the action taken.

#### Order
- **userId** (string): User ID.
- **stock** (string): Stock name.
- **quantity** (integer): Quantity of stock.
- **type** (string): Order type (buy or sell).

#### OrderResponse
- **message** (string): Description of the action taken.

#### TradeRequest
- **from_user** (string): User ID of the sender.
- **to_user** (string): User ID of the receiver.
- **stock** (string): Stock to be traded.
- **quantity** (integer): Quantity of stock to be traded.
- **price** (number): Proposed price per stock.
- **type** (string): Type of trade (buy or sell).

#### TradeRequestResponse
- **message** (string): Description of the action taken.
- **request_id** (string): Unique identifier for the trade request.

#### InboxResponse
- **inbox** (object): List of pending trade requests for the user.

#### TradeResponse
- **request_id** (string): ID of the trade request