using System;
using System.Runtime.InteropServices;

namespace GSCX.Spoofing
{
    public static class SpoofingInterop
    {
        private static IntPtr ToUtf8(string s)
        {
            return Marshal.StringToCoTaskMemUTF8(s);
        }

        [UnmanagedCallersOnly(EntryPoint = "GSCX_GetBoardModel")]
        public static IntPtr GSCX_GetBoardModel()
        {
            return ToUtf8(HardwareSpoof.GetBoardModel());
        }

        [UnmanagedCallersOnly(EntryPoint = "GSCX_GetRegion")]
        public static IntPtr GSCX_GetRegion()
        {
            return ToUtf8(HardwareSpoof.GetRegion());
        }

        [UnmanagedCallersOnly(EntryPoint = "GSCX_GetRandomId")]
        public static IntPtr GSCX_GetRandomId()
        {
            var guid = Guid.NewGuid().ToString();
            return ToUtf8(guid);
        }

        [UnmanagedCallersOnly(EntryPoint = "GSCX_Free")]
        public static void GSCX_Free(IntPtr p)
        {
            if (p != IntPtr.Zero)
            {
                Marshal.FreeCoTaskMem(p);
            }
        }
    }
}