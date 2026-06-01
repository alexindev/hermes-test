const API_BASE = '/api';

export interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  store_name: string | null;
  category_name: string | null;
  avg_rating: number | null;
  review_count: number;
}

export interface ProductDetail extends Product {
  seller_name: string | null;
  reviews: Array<{ id: string; rating: number; created_at: string | null }>;
}

export interface Category {
  id: string;
  name: string;
  product_count: number;
}

export interface Store {
  id: string;
  name: string;
  seller_name: string | null;
  product_count: number;
}

export interface Seller {
  id: string;
  name: string;
  email: string;
  store_count: number;
  product_count: number;
  rating: number | null;
  review_count: number;
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function getProducts(params: {
  category_id?: string;
  search?: string;
  sort?: string;
  page?: number;
  limit?: number;
}): Promise<Product[]> {
  const q = new URLSearchParams();
  if (params.category_id) q.set('category_id', params.category_id);
  if (params.search) q.set('search', params.search);
  if (params.sort) q.set('sort', params.sort);
  if (params.page) q.set('page', String(params.page));
  if (params.limit) q.set('limit', String(params.limit));
  return fetchJSON(`${API_BASE}/products?${q.toString()}`);
}

export async function getProduct(id: string): Promise<ProductDetail> {
  return fetchJSON(`${API_BASE}/products/${id}`);
}

export async function getCategories(): Promise<Category[]> {
  return fetchJSON(`${API_BASE}/categories`);
}

export async function getStores(): Promise<Store[]> {
  return fetchJSON(`${API_BASE}/stores`);
}

export async function getSellers(): Promise<Seller[]> {
  return fetchJSON(`${API_BASE}/sellers`);
}

export async function getSeller(id: string): Promise<Seller> {
  return fetchJSON(`${API_BASE}/sellers/${id}`);
}
