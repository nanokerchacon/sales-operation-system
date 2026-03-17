import { useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { productsApi } from "../services/productsApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { normalizeCollection } from "../utils/apiData";
import { useAsyncData } from "../utils/useAsyncData";

function normalizeProductRows(value) {
  return normalizeCollection(value).map((product, index) => {
    const numericId = Number(product?.id);
    const rawPrice = product?.unit_price ?? product?.price ?? null;
    const numericPrice = Number(rawPrice);

    return {
      id: Number.isFinite(numericId) && numericId > 0 ? numericId : `product-${index}`,
      sku: String(product?.sku || product?.reference || product?.code || "Sin referencia"),
      name: String(product?.name || product?.title || "Producto sin nombre"),
      description: String(product?.description || product?.details || ""),
      legacy_code: String(product?.legacy_code || product?.legacyCode || ""),
      unit_price: Number.isFinite(numericPrice) ? numericPrice : null,
      created_at: product?.created_at || product?.updated_at || null,
    };
  });
}

function buildKpis(products) {
  const totalProducts = products.length;
  const pricedProducts = products.filter((product) => product.unit_price != null);
  const withPrice = pricedProducts.length;
  const avgPrice = withPrice ? pricedProducts.reduce((sum, product) => sum + product.unit_price, 0) / withPrice : 0;
  const withLegacyCode = products.filter((product) => product.legacy_code).length;

  return [
    {
      title: "Productos visibles",
      value: formatInteger(totalProducts),
      detail: "Maestro de producto disponible en esta sesion.",
    },
    {
      title: "Con precio",
      value: formatInteger(withPrice),
      detail: "Productos con tarifa informada en el sistema.",
    },
    {
      title: "Precio medio",
      value: withPrice ? formatCurrency(avgPrice) : "-",
      detail: "Media calculada sobre productos con precio informado.",
    },
    {
      title: "Con codigo legado",
      value: formatInteger(withLegacyCode),
      detail: "Productos enlazados con referencia historica.",
    },
  ];
}

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("name_asc");
  const { data: productsResponse, loading, error } = useAsyncData(productsApi.list, []);

  const products = useMemo(() => normalizeProductRows(productsResponse), [productsResponse]);

  const filteredProducts = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? products.filter((product) =>
          [product.name, product.sku, product.legacy_code, product.description]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(normalizedSearch)),
        )
      : products;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "price_desc") {
        return Number(right.unit_price || 0) - Number(left.unit_price || 0);
      }
      if (sort === "created_desc") {
        return new Date(right.created_at || 0) - new Date(left.created_at || 0);
      }
      return String(left.name || "").localeCompare(String(right.name || ""), "es");
    });
    return rows;
  }, [products, search, sort]);

  const columns = [
    {
      key: "sku",
      header: "Referencia",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.sku}</p>
          <p className="text-xs text-slate-500">ID {row.id}</p>
        </div>
      ),
    },
    {
      key: "name",
      header: "Producto",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">{row.name}</p>
          <p className="text-xs text-slate-500 line-clamp-1">{row.description || "Sin descripcion"}</p>
        </div>
      ),
    },
    {
      key: "legacy_code",
      header: "Codigo legado",
      render: (row) => row.legacy_code || "-",
    },
    {
      key: "unit_price",
      header: "Precio",
      render: (row) => (row.unit_price != null ? formatCurrency(row.unit_price) : "-"),
    },
    {
      key: "created_at",
      header: "Alta",
      render: (row) => formatDate(row.created_at),
    },
  ];

  return (
    <>
      <Header title="Productos" subtitle="Maestro de productos con referencias, descripcion y precio disponible para la operativa diaria." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el modulo de productos." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />)
            : buildKpis(products).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de productos"
            subtitle="Listado estable del maestro de articulos preparado para seguir ampliando el modulo."
            action={
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por referencia, nombre o descripcion"
                  className="w-full min-w-[260px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="name_asc">Nombre</option>
                  <option value="price_desc">Mayor precio</option>
                  <option value="created_desc">Mas recientes</option>
                </select>
              </div>
            }
          >
            {loading ? (
              <LoadingState lines={6} />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredProducts}
                rowKey="id"
                emptyTitle="Sin productos visibles"
                emptyDescription="No hay productos disponibles o la busqueda actual no devuelve resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
