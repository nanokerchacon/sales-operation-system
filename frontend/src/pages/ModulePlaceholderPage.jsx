import EmptyState from "../components/EmptyState";
import Header from "../components/Header";

export default function ModulePlaceholderPage({ title, description }) {
  return (
    <>
      <Header title={title} subtitle={description} />
      <main className="flex-1 px-8 py-8">
        <EmptyState
          title="Módulo preparado"
          description="La base de navegación y permisos ya está activa. La funcionalidad completa de este módulo se desarrollará en la siguiente fase."
        />
      </main>
    </>
  );
}
