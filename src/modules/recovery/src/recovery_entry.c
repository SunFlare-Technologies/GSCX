/*
 * Recovery Entry Point - C implementation
 * Replaces x64 MASM assembly for cross-compiler compatibility
 */

#ifdef __cplusplus
extern "C" {
#endif

/* Forward declaration of the C++ main function */
extern void GSCX_RecoveryMain(void);

/* Exported entry point - replaces assembly version */
#ifdef _WIN32
__declspec(dllexport)
#else
__attribute__((visibility("default")))
#endif
void GSCX_RecoveryEntry(void)
{
    /* Simply call the C++ main function */
    GSCX_RecoveryMain();
}

#ifdef __cplusplus
}
#endif