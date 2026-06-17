export default function FormularioRegistro() {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/30">
      <div className="bg-white w-[600px] rounded-lg shadow-lg p-6">

        {/* Título */}
        <h2 className="text-xl font-semibold border-b pb-2 mb-4">
          Solicitar Registro Consumidor
        </h2>

        {/* Texto */}
        <p className="text-sm text-gray-600 mb-6">
          Rellene el siguiente formulario para enviar por correo electrónico
          una solicitud de registro de consumo.
        </p>

        {/* Formulario */}
        <form className="space-y-4">

          {/* Nombre */}
          <div>
            <label className="block text-sm font-medium">
              Nombre *
            </label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium">
              Correo Electrónico *
            </label>
            <input
              type="email"
              className="w-full border border-gray-300 rounded px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* CUPS */}
          <div>
            <label className="block text-sm font-medium">
              CUPS *
            </label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          {/* ID Comunidad */}
          <div>
            <label className="block text-sm font-medium">
              Id. Comunidad *
            </label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          {/* Checkbox */}
          <div className="flex items-center gap-2">
            <input type="checkbox" />
            <span className="text-sm text-blue-600 cursor-pointer">
              Aceptar términos y condiciones
            </span>
          </div>

          {/* Botones */}
          <div className="flex justify-between pt-4">
            <button
              type="button"
              className="bg-black text-white px-4 py-2 rounded"
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="bg-gray-400 text-white px-4 py-2 rounded"
            >
              Enviar
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
